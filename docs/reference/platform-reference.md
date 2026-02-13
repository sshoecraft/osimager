# Platform Reference

OSImager supports 13 platforms through Packer builder plugins. Each platform is defined by a JSON configuration file in `osimager/data/platforms/` that specifies the Packer builder type, hardware defaults, credential requirements, and template variables.

## Overview

Platforms fall into four categories based on how they build images:

| Category | Platforms | Boot Method | Where It Builds |
|----------|-----------|-------------|-----------------|
| **Local ISO** | virtualbox, vmware, qemu, libvirt, hyperv, xenserver | Boots from ISO | Local workstation |
| **Enterprise ISO** | vsphere, proxmox | Boots from ISO | Remote hypervisor |
| **Cloud** | azure, gcp, aws | Marketplace image (no ISO) | Cloud provider |
| **Special** | none | N/A | Provisioning only |

**Local ISO** platforms boot a VM from an ISO on the local machine, run the installer via boot commands, then provision over SSH/WinRM. The built VM stays registered on the local hypervisor.

**Enterprise ISO** platforms boot a VM from an ISO on a remote hypervisor (vCenter/ESXi or Proxmox VE), run the same installer flow, and store the resulting VM or template on the remote infrastructure. They require platform credentials (server, username, password) stored in your secrets or Vault.

**Cloud** platforms do not use ISOs or boot commands. They launch a marketplace base image, provision it over SSH through a bastion host, then capture the result as a managed image or AMI. They require cloud provider credentials (service principal, access keys, etc.).

**Special** -- the `none` platform uses Packer's null builder. It does not create a VM at all. It exists for running provisioners against an existing host.

---

## Base Defaults (all.json)

Every platform (except `none`) includes `all.json` via the `"include": "all"` directive. This establishes the baseline hardware defaults that all platforms inherit:

```json
{
  "defs": {
    "cpu_sockets": 1,
    "cpu_cores": 2,
    "memory": 2048,
    "boot_disk_size": 16385
  }
}
```

| Default | Value | Description |
|---------|-------|-------------|
| `cpu_sockets` | `1` | Number of CPU sockets |
| `cpu_cores` | `2` | Number of cores per socket |
| `memory` | `2048` | Memory in MB |
| `boot_disk_size` | `16385` | Boot disk size in MB (~16 GB) |

These can be overridden at any layer: platform JSON, location defs, spec defs, or CLI `--define`.

---

## Template Variable Syntax

Platform JSON files use OSImager's template engine markers. The most common patterns found in platform configs:

| Marker | Type | Example | Description |
|--------|------|---------|-------------|
| `>>var<<` | String substitution | `>>name<<` | Replaced with the value of `var` from defs |
| `#>expr<#` | Numeric expression | `#>cpu_sockets*cpu_cores<#` | Evaluates arithmetic on defs values, returns int |
| `%>var<%` | Value replacement | `%>cd_files<%` | Replaced with raw value (preserves type: list, bool, etc.) |
| `E>expr<E` | Python eval | `E>'text' if >>cond<< else 'other'<E` | Evaluates a Python expression after `>>var<<` substitution |

See the [Template Engine](../architecture/template-engine.md) documentation for the complete reference.

---

## Local ISO Platforms

Local ISO platforms run a hypervisor on the build machine, boot a VM from an ISO, and use Packer boot commands to drive the unattended installer. They define `local: true` in defs and store built VMs under `>>vms_path<</<platform>/>>name<<`.

### Common Traits

All local ISO platforms share these characteristics:

- **Include**: `all.json` (inherits base hardware defaults)
- **Defs**: `local: true`
- **Boot method**: ISO boot with `boot_command` from spec
- **Credentials**: No platform credentials required (only `images/<os>` for SSH/WinRM)
- **Location defs needed**: `vms_path`, `iso_path`
- **ISO handling**: Conditional expression selects local path or download URL based on `local_only`

The common ISO URL pattern used across local platforms:

```json
"iso_url": "E>'>>iso_path<</>>iso_name<<' if >>local_only<< else '>>iso_url<<'<E"
```

This evaluates to the local ISO path when `local_only` is true, or the remote download URL otherwise.

---

### VirtualBox

| | |
|---|---|
| **Platform file** | `platforms/virtualbox.json` |
| **Packer builder type** | `virtualbox-iso` |
| **Packer plugin** | `github.com/hashicorp/virtualbox` |
| **Platform type** | Local ISO |
| **Architectures** | i386, x86_64 |

**Plugin install:**
```bash
packer plugins install github.com/hashicorp/virtualbox
```

#### Defs

| Def | Value | Description |
|-----|-------|-------------|
| `local` | `true` | Marks this as a local platform |

Plus inherited from `all.json`: `cpu_sockets`, `cpu_cores`, `memory`, `boot_disk_size`.

#### Config Keys

| Key | Value | Description |
|-----|-------|-------------|
| `type` | `virtualbox-iso` | Packer builder type |
| `vm_name` | `>>name<<` | VM name from build spec |
| `output_directory` | `>>vms_path<</vbox/>>name<<` | Output path for VM files |
| `headless` | `true` | Run without GUI |
| `skip_export` | `true` | Do not export to OVA |
| `keep_registered` | `true` | Keep VM in VirtualBox after build |
| `disable_shutdown` | `false` | Allow graceful shutdown |
| `guest_additions_mode` | `disable` | Do not install guest additions |
| `cpus` | `#>cpu_sockets*cpu_cores<#` | Total vCPU count |
| `memory` | `#>memory<#` | Memory in MB |
| `firmware` | `>>firmware<<` | BIOS or EFI |
| `gfx_controller` | `vmsvga` | Graphics controller type |
| `gfx_vram_size` | `32` | Video memory in MB |
| `usb` | `true` | Enable USB controller |
| `iso_url` | (conditional expression) | ISO source path or URL |
| `iso_checksum` | (conditional expression) | ISO checksum or `none` |
| `iso_target_path` | (conditional expression) | Local download target |
| `cd_files` | `%>cd_files<%` | Files to include on CD |
| `cd_label` | `>>cd_label<<` | CD volume label |
| `hard_drive_discard` | `true` | Enable TRIM/discard |
| `hard_drive_nonrotational` | `true` | Advertise as SSD |
| `hard_drive_interface` | `virtio` | Disk bus type |
| `disk_size` | `#>boot_disk_size<#` | Disk size in MB |
| `skip_nat_mapping` | `true` | Do not set up NAT port forwarding |

#### VBoxManage Commands

VirtualBox uses post-create `vboxmanage` commands to configure VM settings that cannot be set through the builder directly:

1. **movevm** -- Moves the VM to `>>vms_path<</vbox`
2. **modifyvm** (networking) -- Sets NIC 1 to virtio type, bridged mode on `vbnet`
3. **modifyvm** (CPU/hardware) -- Enables IOAPIC, UTC RTC, hardware virtualization (VT-x), VPID, and nested paging

#### Location Defs Needed

| Def | Description |
|-----|-------------|
| `vms_path` | Base path for VM output (VMs stored under `vms_path/vbox/`) |
| `iso_path` | Directory containing OS ISOs |

---

### VMware Workstation/Fusion

| | |
|---|---|
| **Platform file** | `platforms/vmware.json` |
| **Packer builder type** | `vmware-iso` |
| **Packer plugin** | `github.com/hashicorp/vmware` |
| **Platform type** | Local ISO |
| **Architectures** | i386, x86_64 |

**Plugin install:**
```bash
packer plugins install github.com/hashicorp/vmware
```

#### Defs

| Def | Value | Description |
|-----|-------|-------------|
| `local` | `true` | Marks this as a local platform |

Plus inherited from `all.json`: `cpu_sockets`, `cpu_cores`, `memory`, `boot_disk_size`.

#### Config Keys

| Key | Value | Description |
|-----|-------|-------------|
| `type` | `vmware-iso` | Packer builder type |
| `vm_name` | `>>name<<` | VM name |
| `output_directory` | `>>vms_path<</vmware/>>name<<` | Output path for VM files |
| `insecure_connection` | `true` | Skip TLS verification |
| `headless` | `false` | Show GUI during build |
| `skip_export` | `true` | Do not export to OVA |
| `skip_compaction` | `true` | Do not compact disk after build |
| `keep_registered` | `true` | Keep VM registered after build |
| `cpus` | `#>cpu_sockets*cpu_cores<#` | Total vCPU count |
| `cores` | `#>cpu_cores<#` | Cores per socket |
| `memory` | `#>memory<#` | Memory in MB |
| `firmware` | `>>firmware<<` | BIOS or EFI |
| `usb` | `true` | Enable USB controller |
| `iso_url` | (conditional expression) | ISO source path or URL |
| `iso_checksum` | (conditional expression) | ISO checksum or `none` |
| `iso_target_path` | (conditional expression) | Local download target |
| `cd_files` | `%>cd_files<%` | Files to include on CD |
| `cd_label` | `>>cd_label<<` | CD volume label |
| `cdrom_adapter_type` | `ide` | CD-ROM bus type |
| `disk_adapter_type` | `scsi` | Disk bus type |
| `disk_type_id` | `0` | Disk type (0 = growable single file) |
| `disk_size` | `#>boot_disk_size<#` | Disk size in MB |
| `network_adapter_type` | `vmxnet3` | Network adapter type |
| `vnc_disable_password` | `true` | No VNC password |

!!! note
    VMware Workstation/Fusion runs with `headless: false` by default, unlike most other local platforms. This is because VMware Workstation's headless mode has compatibility limitations on some host operating systems.

#### Location Defs Needed

| Def | Description |
|-----|-------------|
| `vms_path` | Base path for VM output (VMs stored under `vms_path/vmware/`) |
| `iso_path` | Directory containing OS ISOs |

---

### QEMU

| | |
|---|---|
| **Platform file** | `platforms/qemu.json` |
| **Packer builder type** | `qemu` |
| **Packer plugin** | `github.com/hashicorp/qemu` |
| **Platform type** | Local ISO |
| **Architectures** | x86_64 only |

**Plugin install:**
```bash
packer plugins install github.com/hashicorp/qemu
```

#### Defs

Inherits from `all.json` only: `cpu_sockets`, `cpu_cores`, `memory`, `boot_disk_size`.

!!! note
    QEMU does not define `local: true` in its defs. It also does not include `cd_files` or `cd_label` in its config, unlike most other ISO-based platforms.

#### Config Keys

| Key | Value | Description |
|-----|-------|-------------|
| `type` | `qemu` | Packer builder type |
| `vm_name` | `>>name<<` | VM name |
| `output_directory` | `>>vms_path<</qemu/>>name<<` | Output path |
| `shutdown_command` | `echo 'packer' \| sudo -S shutdown -P now` | Shutdown via sudo |
| `sockets` | `#>cpu_sockets<#` | CPU sockets |
| `cores` | `#>cpu_cores<#` | Cores per socket |
| `memory` | `#>memory<#` | Memory in MB |
| `firmware` | `>>firmware<<` | BIOS or EFI firmware path |
| `disk_size` | `>>boot_disk_size<<M` | Disk size with M suffix |
| `format` | `qcow2` | Disk image format |
| `accelerator` | `kvm` | Hardware acceleration |
| `http_directory` | `path/to/httpdir` | HTTP directory for kickstart |
| `iso_url` | (conditional expression) | ISO source path or URL |
| `iso_checksum` | (conditional expression) | ISO checksum or `none` |
| `iso_target_path` | (conditional expression) | Local download target |
| `net_device` | `virtio-net` | Network device type |
| `disk_interface` | `virtio` | Disk bus type |

!!! info
    QEMU uses string-based disk size (`>>boot_disk_size<<M`) rather than a numeric expression, since the QEMU builder expects a string with unit suffix.

#### Location Defs Needed

| Def | Description |
|-----|-------------|
| `vms_path` | Base path for VM output (VMs stored under `vms_path/qemu/`) |
| `iso_path` | Directory containing OS ISOs |

---

### Libvirt

| | |
|---|---|
| **Platform file** | `platforms/libvirt.json` |
| **Packer builder type** | `qemu` |
| **Packer plugin** | `github.com/hashicorp/qemu` |
| **Platform type** | Local ISO |
| **Architectures** | x86_64 only |

**Plugin install:**
```bash
packer plugins install github.com/hashicorp/qemu
```

Libvirt uses the same `qemu` Packer builder as the QEMU platform, but is configured as a separate platform for organizational purposes. Output goes to a `libvirt/` subdirectory instead of `qemu/`.

#### Defs

| Def | Value | Description |
|-----|-------|-------------|
| `local` | `true` | Marks this as a local platform |

Plus inherited from `all.json`: `cpu_sockets`, `cpu_cores`, `memory`, `boot_disk_size`.

#### Config Keys

| Key | Value | Description |
|-----|-------|-------------|
| `type` | `qemu` | Packer builder type (same as QEMU) |
| `vm_name` | `>>name<<` | VM name |
| `output_directory` | `>>vms_path<</libvirt/>>name<<` | Output path |
| `sockets` | `#>cpu_sockets<#` | CPU sockets |
| `cores` | `#>cpu_cores<#` | Cores per socket |
| `memory` | `#>memory<#` | Memory in MB |
| `firmware` | `>>firmware<<` | BIOS or EFI firmware path |
| `disk_size` | `>>boot_disk_size<<M` | Disk size with M suffix |
| `format` | `qcow2` | Disk image format |
| `accelerator` | `kvm` | Hardware acceleration |
| `iso_url` | (conditional expression) | ISO source path or URL |
| `iso_checksum` | (conditional expression) | ISO checksum or `none` |
| `iso_target_path` | (conditional expression) | Local download target |
| `cd_files` | `%>cd_files<%` | Files to include on CD |
| `cd_label` | `>>cd_label<<` | CD volume label |
| `net_device` | `virtio-net` | Network device type |
| `disk_interface` | `virtio` | Disk bus type |

#### Location Defs Needed

| Def | Description |
|-----|-------------|
| `vms_path` | Base path for VM output (VMs stored under `vms_path/libvirt/`) |
| `iso_path` | Directory containing OS ISOs |

---

### Hyper-V

| | |
|---|---|
| **Platform file** | `platforms/hyperv.json` |
| **Packer builder type** | `hyperv-iso` |
| **Packer plugin** | `github.com/hashicorp/hyperv` |
| **Platform type** | Local ISO |
| **Architectures** | x86_64 only |

**Plugin install:**
```bash
packer plugins install github.com/hashicorp/hyperv
```

#### Defs

| Def | Value | Description |
|-----|-------|-------------|
| `local` | `true` | Marks this as a local platform |
| `switch_name` | `Default Switch` | Hyper-V virtual switch name |
| `hyperv_generation` | `2` | Hyper-V VM generation |

Plus inherited from `all.json`: `cpu_sockets`, `cpu_cores`, `memory`, `boot_disk_size`.

#### Config Keys

| Key | Value | Description |
|-----|-------|-------------|
| `type` | `hyperv-iso` | Packer builder type |
| `vm_name` | `>>name<<` | VM name |
| `output_directory` | `>>vms_path<</hyperv/>>name<<` | Output path |
| `headless` | `true` | Run without GUI |
| `enable_secure_boot` | `false` | Disable Secure Boot |
| `generation` | `#>hyperv_generation<#` | VM generation (1 or 2) |
| `cpus` | `#>cpu_sockets*cpu_cores<#` | Total vCPU count |
| `memory` | `#>memory<#` | Memory in MB |
| `iso_url` | (conditional expression) | ISO source path or URL |
| `iso_checksum` | (conditional expression) | ISO checksum or `none` |
| `iso_target_path` | (conditional expression) | Local download target |
| `cd_files` | `%>cd_files<%` | Files to include on CD |
| `cd_label` | `>>cd_label<<` | CD volume label |
| `switch_name` | `>>switch_name<<` | Virtual switch name |
| `disk_size` | `#>boot_disk_size<#` | Disk size in MB |

!!! tip
    Override `switch_name` in your location defs if you use a virtual switch other than `Default Switch`. Override `hyperv_generation` to `1` if building legacy BIOS-only operating systems.

#### Location Defs Needed

| Def | Description |
|-----|-------------|
| `vms_path` | Base path for VM output (VMs stored under `vms_path/hyperv/`) |
| `iso_path` | Directory containing OS ISOs |

---

### XenServer

| | |
|---|---|
| **Platform file** | `platforms/xenserver.json` |
| **Packer builder type** | `xenserver-iso` |
| **Packer plugin** | `github.com/ddelnano/xenserver` |
| **Platform type** | Local ISO |
| **Architectures** | x86_64 only |

**Plugin install:**
```bash
packer plugins install github.com/ddelnano/xenserver
```

#### Defs

| Def | Value | Description |
|-----|-------|-------------|
| `local` | `true` | Marks this as a local platform |

Plus inherited from `all.json`: `cpu_sockets`, `cpu_cores`, `memory`, `boot_disk_size`.

#### Config Keys

| Key | Value | Description |
|-----|-------|-------------|
| `type` | `xenserver-iso` | Packer builder type |
| `vm_name` | `>>name<<` | VM name |
| `output_directory` | `>>vms_path<</xen/>>name<<` | Output path |
| `headless` | `true` | Run without GUI |
| `skip_export` | `true` | Do not export to XVA |
| `keep_registered` | `true` | Keep VM registered |
| `disable_shutdown` | `false` | Allow graceful shutdown |
| `guest_additions_mode` | `disable` | Do not install guest tools |
| `cpus` | `#>cpu_sockets*cpu_cores<#` | Total vCPU count |
| `memory` | `#>memory<#` | Memory in MB |
| `usb` | `true` | Enable USB controller |
| `iso_url` | (conditional expression) | ISO source path or URL |
| `iso_checksum` | (conditional expression) | ISO checksum or `none` |
| `iso_target_path` | (conditional expression) | Local download target |
| `cd_files` | `%>cd_files<%` | Files to include on CD |
| `cd_label` | `>>cd_label<<` | CD volume label |
| `hard_drive_interface` | `virtio` | Disk bus type |
| `disk_size` | `#>boot_disk_size<#` | Disk size in MB |
| `skip_nat_mapping` | `true` | Do not set up NAT port forwarding |

#### Location Defs Needed

| Def | Description |
|-----|-------------|
| `vms_path` | Base path for VM output (VMs stored under `vms_path/xen/`) |
| `iso_path` | Directory containing OS ISOs |

---

## Enterprise ISO Platforms

Enterprise platforms boot VMs from ISOs on remote hypervisors. They require platform credentials and infrastructure-specific location defs (datacenter, datastore, storage pools, etc.).

---

### vSphere

| | |
|---|---|
| **Platform file** | `platforms/vsphere.json` |
| **Packer builder type** | `vsphere-iso` |
| **Packer plugin** | `github.com/hashicorp/vsphere` |
| **Platform type** | Enterprise ISO |
| **Architectures** | i386, x86_64 |

**Plugin install:**
```bash
packer plugins install github.com/hashicorp/vsphere
```

#### Defs

| Def | Value | Description |
|-----|-------|-------------|
| `vm_network` | `VM Network` | vSphere port group name for VM networking |
| `thin_disk` | `false` | Whether to thin-provision the boot disk |

Plus inherited from `all.json`: `cpu_sockets`, `cpu_cores`, `memory`, `boot_disk_size`.

#### Variables (Credential References)

vSphere uses Packer variables populated from Vault/secrets:

| Variable | Vault Path | Description |
|----------|------------|-------------|
| `vsphere-server` | `vsphere/>>location_name<< : server` | vCenter/ESXi server address |
| `vsphere-username` | `vsphere/>>location_name<< : username` | vSphere login username |
| `vsphere-password` | `vsphere/>>location_name<< : password` | vSphere login password |

The `>>location_name<<` is substituted with the location name from the build target (e.g., `lab`).

#### Config Keys

| Key | Value | Description |
|-----|-------|-------------|
| `type` | `vsphere-iso` | Packer builder type |
| `vcenter_server` | `{{user "vsphere-server"}}` | vCenter address from variable |
| `username` | `{{user "vsphere-username"}}` | Login username from variable |
| `password` | `{{user "vsphere-password"}}` | Login password from variable |
| `datacenter` | `>>datacenter<<` | vSphere datacenter |
| `host` | `>>esxi_host<<` | Target ESXi host |
| `cluster` | `>>cluster<<` | vSphere cluster |
| `datastore` | `>>datastore<<` | Target datastore |
| `folder` | `>>folder<<` | vCenter folder for the VM |
| `insecure_connection` | `true` | Skip TLS certificate verification |
| `convert_to_template` | `false` | Do not convert to template after build |
| `vm_name` | `>>name<<` | VM name |
| `CPUs` | `#>cpu_sockets*cpu_cores<#` | Total vCPU count |
| `cpu_cores` | `0` | Cores per socket (0 = assign at power on) |
| `CPU_hot_plug` | `false` | Disable CPU hot-add |
| `RAM` | `#>memory<#` | Memory in MB |
| `RAM_hot_plug` | `false` | Disable memory hot-add |
| `RAM_reserve_all` | `false` | Do not reserve all memory |
| `firmware` | `>>firmware<<` | BIOS or EFI |
| `iso_url` | (conditional expression) | ISO source path or URL |
| `iso_checksum` | (conditional expression) | ISO checksum or `none` |
| `iso_target_path` | `>>iso_path<</>>iso_name<<` | Datastore path for ISO |
| `cd_files` | `%>cd_files<%` | Files to include on CD |
| `cd_label` | `>>cd_label<<` | CD volume label |
| `usb_controller` | `usb` | USB controller type |
| `remove_cdrom` | `true` | Remove CD-ROM after build |
| `network_adapters` | (see below) | Network adapter configuration |
| `disk_controller_type` | `pvscsi` | Paravirtual SCSI controller |
| `storage` | (see below) | Disk layout |
| `iso_paths` | (see below) | VMware Tools ISO |

**Network adapters:**

```json
"network_adapters": [
  {
    "network": ">>vm_network<<",
    "network_card": "vmxnet3"
  }
]
```

**Storage:**

```json
"storage": [
  {
    "disk_size": "#>boot_disk_size<#",
    "disk_thin_provisioned": "%>thin_disk<%"
  }
]
```

**VMware Tools ISO path:**

```json
"iso_paths": [
  "[] /vmimages/tools-isoimages/E>'windows' if '>>spec_name<<'.startswith('win') else 'linux'<E.iso"
]
```

This dynamically selects the Windows or Linux VMware Tools ISO based on the spec name.

!!! note "CPU topology"
    The `cpu_cores` config key is set to `0`, meaning the CPU topology (sockets vs. cores) is assigned at power on rather than baked into the VM configuration. The total CPU count is still controlled by the `CPUs` key.

#### Location Defs Needed

| Def | Required | Description |
|-----|----------|-------------|
| `datacenter` | Yes | vSphere datacenter name |
| `esxi_host` | Yes | Target ESXi host FQDN or IP |
| `cluster` | Yes | vSphere cluster name |
| `datastore` | Yes | Datastore for VM storage |
| `folder` | Yes | vCenter folder path |
| `iso_path` | Yes | Datastore path for ISO files |
| `vm_network` | No | Port group name (default: `VM Network`) |
| `thin_disk` | No | Thin provisioning (default: `false`) |

#### Credential Requirements

Secret path: `vsphere/<location>`

| Key | Description |
|-----|-------------|
| `server` | vCenter or ESXi hostname |
| `username` | vSphere login (e.g., `administrator@vsphere.local`) |
| `password` | vSphere password |

---

### Proxmox

| | |
|---|---|
| **Platform file** | `platforms/proxmox.json` |
| **Packer builder type** | `proxmox-iso` |
| **Packer plugin** | `github.com/hashicorp/proxmox` |
| **Platform type** | Enterprise ISO |
| **Architectures** | i386, x86_64 |

**Plugin install:**
```bash
packer plugins install github.com/hashicorp/proxmox
```

#### Defs

| Def | Value | Description |
|-----|-------|-------------|
| `shutcmd` | `false` | Disables the default shutdown command (Proxmox handles shutdown via QEMU agent) |

Plus inherited from `all.json`: `cpu_sockets`, `cpu_cores`, `memory`, `boot_disk_size`.

#### Variables (Credential References)

| Variable | Vault Path | Description |
|----------|------------|-------------|
| `proxmox-server` | `proxmox/>>location_name<< : server` | Proxmox server hostname |
| `proxmox-username` | `proxmox/>>location_name<< : username` | Proxmox login username |
| `proxmox-password` | `proxmox/>>location_name<< : password` | Proxmox login password |
| `name` | `{{ build_name }}` | Packer build name (used internally) |

#### Config Keys

| Key | Value | Description |
|-----|-------|-------------|
| `type` | `proxmox-iso` | Packer builder type |
| `node` | `>>proxmox_node<<` | Target Proxmox node |
| `proxmox_url` | `https://{{user "proxmox-server"}}:8006/api2/json` | Proxmox API endpoint |
| `username` | `{{user "proxmox-username"}}` | Login username from variable |
| `password` | `{{user "proxmox-password"}}` | Login password from variable |
| `qemu_agent` | `true` | Enable QEMU guest agent |
| `insecure_skip_tls_verify` | `true` | Skip TLS verification |
| `vm_name` | `>>name<<` | VM name |
| `sockets` | `#>cpu_sockets<#` | CPU sockets |
| `cores` | `#>cpu_cores<#` | Cores per socket |
| `cpu_type` | `host` | CPU type passthrough |
| `memory` | `#>memory<#` | Memory in MB |
| `numa` | `true` | Enable NUMA |
| `task_timeout` | `1h` | Proxmox task timeout |
| `boot_iso` | (see below) | Boot ISO configuration |
| `additional_iso_files` | (see below) | Additional CD with kickstart files |
| `network_adapters` | (see below) | Network configuration |
| `scsi_controller` | `virtio-scsi-single` | SCSI controller type |
| `disks` | (see below) | Disk layout |

**Boot ISO:**

```json
"boot_iso": {
  "type": "ide",
  "iso_file|iso_url": "(conditional based on local_only)",
  "iso_download_pve": "(conditional based on local_only)",
  "iso_checksum": "(conditional expression)",
  "iso_target_path": "(conditional expression)",
  "iso_storage_pool": ">>iso_storage_pool<<",
  "unmount": true
}
```

When `local_only` is true, `iso_file` is used with a `local:iso/` path. Otherwise, `iso_url` is used and `iso_download_pve` is enabled so Proxmox downloads the ISO directly.

**Additional ISO files (kickstart CD):**

```json
"additional_iso_files": [
  {
    "type": "ide",
    "cd_files": "%>cd_files<%",
    "cd_label": ">>cd_label<<",
    "unmount": true,
    "iso_storage_pool": ">>iso_storage_pool<<"
  }
]
```

**Network adapters:**

```json
"network_adapters": [
  {
    "model": "virtio",
    "bridge": "vmbr0",
    "firewall": false
  }
]
```

**Disks:**

```json
"disks": [
  {
    "type": "virtio",
    "disk_size": ">>boot_disk_size<<M",
    "storage_pool": ">>vm_storage_pool<<"
  }
]
```

!!! note
    Proxmox sets `shutcmd: false`, which disables the spec-provided shutdown command. Proxmox VE handles VM shutdown through the QEMU guest agent instead.

#### Location Defs Needed

| Def | Required | Description |
|-----|----------|-------------|
| `proxmox_node` | Yes | Proxmox VE node name |
| `iso_storage_pool` | Yes | Storage pool for ISO files (e.g., `local`) |
| `vm_storage_pool` | Yes | Storage pool for VM disks (e.g., `local-lvm`) |
| `iso_path` | Yes | ISO path prefix |

#### Credential Requirements

Secret path: `proxmox/<location>`

| Key | Description |
|-----|-------------|
| `server` | Proxmox server hostname |
| `username` | Proxmox username (e.g., `root@pam`) |
| `password` | Proxmox password |

---

## Cloud Platforms

Cloud platforms do not use ISOs or boot commands. They launch a base image from the cloud marketplace, provision it over SSH (typically through a bastion host), and capture the result as a managed image. All cloud platforms set `boot: false` and `shutcmd: false` in their defs.

### Common Traits

- **No ISO**: No `iso_url`, `cd_files`, or `boot_command`
- **Defs**: `boot: false`, `shutcmd: false`
- **Authentication**: Cloud provider credentials via Vault/secrets
- **SSH access**: Through a bastion host (Azure, GCP) or direct (AWS)
- **Output**: Managed image, AMI, or compute image

---

### Azure

| | |
|---|---|
| **Platform file** | `platforms/azure.json` |
| **Packer builder type** | `azure-arm` |
| **Packer plugin** | `github.com/hashicorp/azure` |
| **Platform type** | Cloud |
| **Architectures** | x86_64 only |

**Plugin install:**
```bash
packer plugins install github.com/hashicorp/azure
```

#### Defs

| Def | Value | Description |
|-----|-------|-------------|
| `boot` | `false` | No boot command (cloud image) |
| `shutcmd` | `false` | No shutdown command |
| `vm_size` | `Standard_D2s_v3` | Azure VM size for the build instance |
| `image_version` | `latest` | Marketplace image version |

Plus inherited from `all.json`: `cpu_sockets`, `cpu_cores`, `memory`, `boot_disk_size`.

#### Variables (Credential References)

| Variable | Vault Path | Description |
|----------|------------|-------------|
| `client-id` | `azure/>>location_name<< : client_id` | Service principal client ID |
| `client-secret` | `azure/>>location_name<< : client_secret` | Service principal secret |
| `tenant-id` | `azure/>>location_name<< : tenant_id` | Azure AD tenant ID |
| `subscription-id` | `azure/>>location_name<< : subscription_id` | Azure subscription ID |
| `gallery-subscription-id` | `azure/>>location_name<< : gallery_subscription_id` | Gallery subscription ID |
| `gallery-resource-group` | `azure/>>location_name<< : gallery_resource_group` | Gallery resource group |
| `gallery-name` | `azure/>>location_name<< : gallery_name` | Shared Image Gallery name |
| `az-bastion-hostname` | `azure/>>location_name<< : bastion_hostname` | Bastion host for SSH |
| `az-bastion-username` | `azure/>>location_name<< : bastion_username` | Bastion username |
| `az-bastion-keyfile` | `azure/>>location_name<< : bastion_keyfile` | Bastion SSH private key file |

#### Config Keys

| Key | Value | Description |
|-----|-------|-------------|
| `type` | `azure-arm` | Packer builder type |
| `client_id` | `{{user "client-id"}}` | Service principal client ID |
| `client_secret` | `{{user "client-secret"}}` | Service principal secret |
| `tenant_id` | `{{user "tenant-id"}}` | Azure AD tenant ID |
| `subscription_id` | `{{user "subscription-id"}}` | Subscription ID |
| `location` | `>>azure_location<<` | Azure region |
| `vm_size` | `>>vm_size<<` | Build VM size |
| `managed_image_name` | `>>name<<` | Output image name |
| `managed_image_resource_group_name` | `>>azure_resource_group<<` | Resource group for the image |
| `temp_resource_group_name` | `rg-packer-build->>name<<->>azure_location<<` | Temp resource group for build |
| `image_publisher` | `>>azure_image_publisher<<` | Marketplace publisher |
| `image_offer` | `>>azure_image_offer<<` | Marketplace offer |
| `image_sku` | `>>azure_image_sku<<` | Marketplace SKU |
| `image_version` | `>>image_version<<` | Marketplace version (default: `latest`) |
| `os_type` | (conditional expression) | `Windows` or `Linux` based on spec name |
| `shared_image_gallery_destination` | (see below) | Gallery publishing config |
| `shared_image_gallery_replica_count` | `2` | Number of gallery replicas |
| `ssh_bastion_host` | `{{user "az-bastion-hostname"}}` | Bastion hostname |
| `ssh_bastion_username` | `{{user "az-bastion-username"}}` | Bastion username |
| `ssh_bastion_private_key_file` | `{{user "az-bastion-keyfile"}}` | Bastion SSH key |
| `ssh_clear_authorized_keys` | `true` | Clean SSH keys from image |
| `ssh_pty` | `true` | Allocate pseudo-terminal |

**Shared Image Gallery destination:**

```json
"shared_image_gallery_destination": {
  "subscription": "{{user `gallery-subscription-id`}}",
  "resource_group": "{{user `gallery-resource-group`}}",
  "gallery_name": "{{user `gallery-name`}}",
  "image_name": ">>name<<",
  "image_version": "{{isotime `2006.01.02`}}",
  "replication_regions": "%>azure_replication_regions<%",
  "storage_account_type": "Standard_LRS"
}
```

The image version uses Packer's `isotime` function with Go date format to produce a date-based version string (e.g., `2024.11.15`).

!!! note
    The `os_type` field uses a Python eval expression to auto-detect Windows vs. Linux: `E>'Windows' if '>>spec_name<<'.startswith('win') else 'Linux'<E`.

#### Location Defs Needed

| Def | Required | Description |
|-----|----------|-------------|
| `azure_location` | Yes | Azure region (e.g., `eastus`) |
| `azure_resource_group` | Yes | Resource group for managed images |
| `azure_image_publisher` | Yes | Marketplace image publisher |
| `azure_image_offer` | Yes | Marketplace image offer |
| `azure_image_sku` | Yes | Marketplace image SKU |
| `azure_replication_regions` | Yes | List of regions for gallery replication |
| `vm_size` | No | Build VM size (default: `Standard_D2s_v3`) |
| `image_version` | No | Marketplace image version (default: `latest`) |

#### Credential Requirements

Secret path: `azure/<location>`

| Key | Description |
|-----|-------------|
| `client_id` | Azure service principal client ID |
| `client_secret` | Azure service principal secret |
| `tenant_id` | Azure AD tenant ID |
| `subscription_id` | Azure subscription ID |
| `gallery_subscription_id` | Shared Image Gallery subscription |
| `gallery_resource_group` | Gallery resource group name |
| `gallery_name` | Shared Image Gallery name |
| `bastion_hostname` | SSH bastion host |
| `bastion_username` | Bastion SSH username |
| `bastion_keyfile` | Bastion SSH private key file path |

---

### GCP (Google Cloud Platform)

| | |
|---|---|
| **Platform file** | `platforms/gcp.json` |
| **Packer builder type** | `googlecompute` |
| **Packer plugin** | `github.com/hashicorp/googlecompute` |
| **Platform type** | Cloud |
| **Architectures** | x86_64 only |

**Plugin install:**
```bash
packer plugins install github.com/hashicorp/googlecompute
```

#### Defs

| Def | Value | Description |
|-----|-------|-------------|
| `boot` | `false` | No boot command (cloud image) |
| `shutcmd` | `false` | No shutdown command |
| `machine_type` | `n1-standard-2` | GCE machine type for the build instance |
| `disk_type` | `pd-ssd` | Persistent disk type |
| `state_timeout` | `15m` | Timeout waiting for instance state changes |

Plus inherited from `all.json`: `cpu_sockets`, `cpu_cores`, `memory`, `boot_disk_size`.

#### Variables (Credential References)

| Variable | Vault Path | Description |
|----------|------------|-------------|
| `gcp-creds` | `gcp/>>location_name<< : credentials_json` | Service account JSON key |
| `project-id` | `gcp/>>location_name<< : project_id` | GCP project ID |
| `service-account-email` | `gcp/>>location_name<< : service_account_email` | Service account email |
| `gcp-bastion-hostname` | `gcp/>>location_name<< : bastion_hostname` | Bastion host for SSH |
| `gcp-bastion-username` | `gcp/>>location_name<< : bastion_username` | Bastion username |
| `gcp-bastion-password` | `gcp/>>location_name<< : bastion_password` | Bastion password |

#### Config Keys

| Key | Value | Description |
|-----|-------|-------------|
| `type` | `googlecompute` | Packer builder type |
| `credentials_json` | `{{user "gcp-creds"}}` | Service account JSON |
| `project_id` | `{{user "project-id"}}` | GCP project |
| `service_account_email` | `{{user "service-account-email"}}` | Service account |
| `region` | `>>gcp_region<<` | GCP region |
| `zone` | `>>gcp_zone<<` | GCP zone |
| `machine_type` | `>>machine_type<<` | Build instance type |
| `disk_type` | `>>disk_type<<` | Disk type (SSD/standard) |
| `instance_name` | `build->>name<<` | Build instance name |
| `image_name` | `>>name<<-{{isotime \| clean_resource_name}}` | Output image name with timestamp |
| `image_family` | `>>gcp_image_family<<` | Image family for the output |
| `image_description` | `>>name<< Image` | Image description |
| `source_image_family` | `>>gcp_source_image_family<<` | Base image family to build from |
| `source_image_project_id` | `>>gcp_source_image_project_id<<` | Project hosting the source image |
| `image_labels` | `{"img-region": ">>gcp_region<<"}` | Labels applied to the output image |
| `state_timeout` | `>>state_timeout<<` | Instance state timeout |
| `ssh_bastion_host` | `{{user "gcp-bastion-hostname"}}` | Bastion hostname |
| `ssh_bastion_username` | `{{user "gcp-bastion-username"}}` | Bastion username |
| `ssh_bastion_password` | `{{user "gcp-bastion-password"}}` | Bastion password |
| `ssh_clear_authorized_keys` | `true` | Clean SSH keys from image |
| `tags` | `["packer"]` | Network tags for firewall rules |

!!! info
    GCP image names are appended with a Packer-generated timestamp via `{{isotime | clean_resource_name}}` to ensure uniqueness, since GCP image names must be globally unique within a project.

#### Location Defs Needed

| Def | Required | Description |
|-----|----------|-------------|
| `gcp_region` | Yes | GCP region (e.g., `us-central1`) |
| `gcp_zone` | Yes | GCP zone (e.g., `us-central1-a`) |
| `gcp_image_family` | Yes | Output image family name |
| `gcp_source_image_family` | Yes | Source image family (e.g., `rhel-9`) |
| `gcp_source_image_project_id` | Yes | Project hosting the source image (e.g., `rhel-cloud`) |
| `machine_type` | No | Build machine type (default: `n1-standard-2`) |
| `disk_type` | No | Persistent disk type (default: `pd-ssd`) |
| `state_timeout` | No | State timeout (default: `15m`) |

#### Credential Requirements

Secret path: `gcp/<location>`

| Key | Description |
|-----|-------------|
| `credentials_json` | Service account JSON key content |
| `project_id` | GCP project ID |
| `service_account_email` | Service account email address |
| `bastion_hostname` | SSH bastion host |
| `bastion_username` | Bastion SSH username |
| `bastion_password` | Bastion SSH password |

---

### AWS (Amazon Web Services)

| | |
|---|---|
| **Platform file** | `platforms/aws.json` |
| **Packer builder type** | `amazon-ebs` |
| **Packer plugin** | `github.com/hashicorp/amazon` |
| **Platform type** | Cloud |
| **Architectures** | x86_64 only |

**Plugin install:**
```bash
packer plugins install github.com/hashicorp/amazon
```

#### Defs

| Def | Value | Description |
|-----|-------|-------------|
| `boot` | `false` | No boot command (cloud image) |
| `shutcmd` | `false` | No shutdown command |
| `instance_type` | `t3.medium` | EC2 instance type for the build |

Plus inherited from `all.json`: `cpu_sockets`, `cpu_cores`, `memory`, `boot_disk_size`.

#### Variables (Credential References)

| Variable | Vault Path | Description |
|----------|------------|-------------|
| `aws-access-key` | `aws/>>location_name<< : access_key` | AWS access key ID |
| `aws-secret-key` | `aws/>>location_name<< : secret_key` | AWS secret access key |

#### Config Keys

| Key | Value | Description |
|-----|-------|-------------|
| `type` | `amazon-ebs` | Packer builder type |
| `access_key` | `{{user "aws-access-key"}}` | AWS access key |
| `secret_key` | `{{user "aws-secret-key"}}` | AWS secret key |
| `region` | `>>aws_region<<` | AWS region |
| `instance_type` | `>>instance_type<<` | Build instance type |
| `ami_name` | `>>name<<-{{isotime "2006-01-02"}}` | AMI name with date |
| `ami_description` | `>>name<< Image` | AMI description |
| `source_ami_filter` | (see below) | Source AMI filter |
| `ssh_clear_authorized_keys` | `true` | Clean SSH keys from image |
| `vpc_id` | `>>aws_vpc_id<<` | VPC for the build instance |
| `subnet_id` | `>>aws_subnet_id<<` | Subnet for the build instance |
| `associate_public_ip_address` | `true` | Assign public IP for SSH access |
| `tags` | `{"Name": ">>name<<", "Builder": "packer"}` | Tags on the AMI |

**Source AMI filter:**

```json
"source_ami_filter": {
  "filters": {
    "name": ">>aws_ami_filter_name<<",
    "root-device-type": "ebs",
    "virtualization-type": "hvm"
  },
  "most_recent": true,
  "owners": "%>aws_ami_owners<%"
}
```

The source AMI is selected dynamically using a name filter pattern and owner list rather than a hardcoded AMI ID. This ensures builds always use the latest base AMI matching the criteria.

!!! note
    AWS is the only cloud platform that does not use a bastion host for SSH. It assigns a public IP directly to the build instance via `associate_public_ip_address: true`.

#### Location Defs Needed

| Def | Required | Description |
|-----|----------|-------------|
| `aws_region` | Yes | AWS region (e.g., `us-east-1`) |
| `aws_vpc_id` | Yes | VPC ID for the build instance |
| `aws_subnet_id` | Yes | Subnet ID for the build instance |
| `aws_ami_filter_name` | Yes | AMI name filter pattern (e.g., `RHEL-9.*_HVM-*-x86_64-*`) |
| `aws_ami_owners` | Yes | List of AMI owner account IDs |
| `instance_type` | No | EC2 instance type (default: `t3.medium`) |

#### Credential Requirements

Secret path: `aws/<location>`

| Key | Description |
|-----|-------------|
| `access_key` | AWS access key ID |
| `secret_key` | AWS secret access key |

---

## Special Platforms

### None (Null Builder)

| | |
|---|---|
| **Platform file** | `platforms/none.json` |
| **Packer builder type** | `null` |
| **Packer plugin** | Built-in (no plugin required) |
| **Platform type** | Special |
| **Architectures** | N/A |

The `none` platform uses Packer's built-in null builder. It does not create a VM, boot from an ISO, or interact with any hypervisor. It exists solely for running provisioners against an existing host over SSH.

#### Defs

| Def | Value | Description |
|-----|-------|-------------|
| `boot` | `false` | No boot command |
| `shutcmd` | `false` | No shutdown command |

!!! warning
    The `none` platform does **not** include `all.json`. It has no hardware defaults (`cpu_sockets`, `cpu_cores`, `memory`, `boot_disk_size` are not set) since no VM is created.

#### Config

```json
{
  "type": "null"
}
```

The config contains only the builder type. All other configuration (SSH host, username, etc.) must be provided through spec defs or CLI `--define` overrides.

#### Location Defs Needed

No location defs are required. The null builder connects to an existing host, so SSH connection details must be provided through other configuration layers.

#### Credential Requirements

No platform credentials are needed. SSH/WinRM credentials for the target host must be provided through the spec or `images/<os>` secrets.

---

## Platform Comparison

### Feature Matrix

| Platform | Builder Type | ISO Boot | Credentials | Bastion | Output Format |
|----------|-------------|----------|-------------|---------|---------------|
| virtualbox | `virtualbox-iso` | Yes | None | No | VDI in `vms_path/vbox/` |
| vmware | `vmware-iso` | Yes | None | No | VMDK in `vms_path/vmware/` |
| qemu | `qemu` | Yes | None | No | qcow2 in `vms_path/qemu/` |
| libvirt | `qemu` | Yes | None | No | qcow2 in `vms_path/libvirt/` |
| hyperv | `hyperv-iso` | Yes | None | No | VHDX in `vms_path/hyperv/` |
| xenserver | `xenserver-iso` | Yes | None | No | VHD in `vms_path/xen/` |
| vsphere | `vsphere-iso` | Yes | `vsphere/<loc>` | No | VM on vSphere datastore |
| proxmox | `proxmox-iso` | Yes | `proxmox/<loc>` | No | VM on Proxmox storage |
| azure | `azure-arm` | No | `azure/<loc>` | Yes | Managed Image + Gallery |
| gcp | `googlecompute` | No | `gcp/<loc>` | Yes | Compute Engine Image |
| aws | `amazon-ebs` | No | `aws/<loc>` | No | AMI |
| none | `null` | No | None | No | N/A |

### Architecture Support

| Platform | i386 | x86_64 |
|----------|------|--------|
| virtualbox | Yes | Yes |
| vmware | Yes | Yes |
| vsphere | Yes | Yes |
| proxmox | Yes | Yes |
| qemu | No | Yes |
| libvirt | No | Yes |
| hyperv | No | Yes |
| xenserver | No | Yes |
| azure | No | Yes |
| gcp | No | Yes |
| aws | No | Yes |
| none | N/A | N/A |

### Disk Configuration

| Platform | Interface | Size Format | Default Format |
|----------|-----------|-------------|----------------|
| virtualbox | virtio | Numeric (MB) | VDI |
| vmware | SCSI | Numeric (MB) | VMDK (type 0) |
| qemu | virtio | String with M suffix | qcow2 |
| libvirt | virtio | String with M suffix | qcow2 |
| hyperv | default | Numeric (MB) | VHDX |
| xenserver | virtio | Numeric (MB) | VHD |
| vsphere | pvscsi | Numeric (MB) | VMDK (thin optional) |
| proxmox | virtio | String with M suffix | Raw/qcow2 |
| azure | N/A | N/A | Managed disk |
| gcp | N/A | N/A | Persistent disk |
| aws | N/A | N/A | EBS |

### Network Configuration

| Platform | Adapter Type | Mode |
|----------|-------------|------|
| virtualbox | virtio | Bridged on `vbnet` |
| vmware | vmxnet3 | Default |
| qemu | virtio-net | Default |
| libvirt | virtio-net | Default |
| hyperv | default | Virtual switch (`>>switch_name<<`) |
| xenserver | default | Default |
| vsphere | vmxnet3 | Port group (`>>vm_network<<`) |
| proxmox | virtio | Bridge `vmbr0` |
| azure | N/A | VNet (managed) |
| gcp | N/A | VPC (managed) |
| aws | N/A | VPC subnet |
