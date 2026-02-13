# Defs Reference

This page is auto-generated from the platform and spec data files. It documents all template variables (defs) used by each platform.

## Base Defaults (all.json)

These defaults are inherited by all platforms:

| Variable | Default Value |
|----------|--------------|
| `boot_disk_size` | `16385` |
| `cpu_cores` | `2` |
| `cpu_sockets` | `1` |
| `memory` | `2048` |

## Local ISO Platforms

### virtualbox

**Builder type:** `virtualbox-iso`

**Platform defs:**

| Variable | Value |
|----------|-------|
| `local` | `True` |

**Template variables referenced** (`>>var<<`):

- `cd_label` — spec
- `firmware` — computed
- `iso_checksum` — spec
- `iso_name` — spec
- `iso_path` — location
- `iso_url` — spec
- `local_only` — computed
- `name` — computed
- `vms_path` — location

**Value replacements** (`%>var<%`):

- `cd_files`

**Numeric expressions** (`#>expr<#`):

- `boot_disk_size`
- `cpu_sockets*cpu_cores`
- `memory`

**Eval expressions** (`E>expr<E`):

- `'' if >>local_only<< else '>>iso_path<</>>iso_name<<'`
- `'>>iso_checksum<<' if len('>>iso_checksum<<') else 'none'`
- `'>>iso_path<</>>iso_name<<' if >>local_only<< else '>>iso_url<<'`

---

### vmware

**Builder type:** `vmware-iso`

**Platform defs:**

| Variable | Value |
|----------|-------|
| `local` | `True` |

**Template variables referenced** (`>>var<<`):

- `cd_label` — spec
- `firmware` — computed
- `iso_checksum` — spec
- `iso_name` — spec
- `iso_path` — location
- `iso_url` — spec
- `local_only` — computed
- `name` — computed
- `vms_path` — location

**Value replacements** (`%>var<%`):

- `cd_files`

**Numeric expressions** (`#>expr<#`):

- `boot_disk_size`
- `cpu_cores`
- `cpu_sockets*cpu_cores`
- `memory`

**Eval expressions** (`E>expr<E`):

- `'' if >>local_only<< else '>>iso_path<</>>iso_name<<'`
- `'>>iso_checksum<<' if len('>>iso_checksum<<') else 'none'`
- `'>>iso_path<</>>iso_name<<' if >>local_only<< else '>>iso_url<<'`

---

### qemu

**Builder type:** `qemu`

**Template variables referenced** (`>>var<<`):

- `boot_disk_size` — all.json default
- `firmware` — computed
- `iso_checksum` — spec
- `iso_name` — spec
- `iso_path` — location
- `iso_url` — spec
- `local_only` — computed
- `name` — computed
- `vms_path` — location

**Numeric expressions** (`#>expr<#`):

- `cpu_cores`
- `cpu_sockets`
- `memory`

**Eval expressions** (`E>expr<E`):

- `'' if >>local_only<< else '>>iso_path<</>>iso_name<<'`
- `'>>iso_checksum<<' if len('>>iso_checksum<<') else 'none'`
- `'>>iso_path<</>>iso_name<<' if >>local_only<< else '>>iso_url<<'`

---

### libvirt

**Builder type:** `qemu`

**Platform defs:**

| Variable | Value |
|----------|-------|
| `local` | `True` |

**Template variables referenced** (`>>var<<`):

- `boot_disk_size` — all.json default
- `cd_label` — spec
- `firmware` — computed
- `iso_checksum` — spec
- `iso_name` — spec
- `iso_path` — location
- `iso_url` — spec
- `local_only` — computed
- `name` — computed
- `vms_path` — location

**Value replacements** (`%>var<%`):

- `cd_files`

**Numeric expressions** (`#>expr<#`):

- `cpu_cores`
- `cpu_sockets`
- `memory`

**Eval expressions** (`E>expr<E`):

- `'' if >>local_only<< else '>>iso_path<</>>iso_name<<'`
- `'>>iso_checksum<<' if len('>>iso_checksum<<') else 'none'`
- `'>>iso_path<</>>iso_name<<' if >>local_only<< else '>>iso_url<<'`

---

### hyperv

**Builder type:** `hyperv-iso`

**Platform defs:**

| Variable | Value |
|----------|-------|
| `hyperv_generation` | `2` |
| `local` | `True` |
| `switch_name` | `Default Switch` |

**Template variables referenced** (`>>var<<`):

- `cd_label` — spec
- `iso_checksum` — spec
- `iso_name` — spec
- `iso_path` — location
- `iso_url` — spec
- `local_only` — computed
- `name` — computed
- `switch_name` — computed
- `vms_path` — location

**Value replacements** (`%>var<%`):

- `cd_files`

**Numeric expressions** (`#>expr<#`):

- `boot_disk_size`
- `cpu_sockets*cpu_cores`
- `hyperv_generation`
- `memory`

**Eval expressions** (`E>expr<E`):

- `'' if >>local_only<< else '>>iso_path<</>>iso_name<<'`
- `'>>iso_checksum<<' if len('>>iso_checksum<<') else 'none'`
- `'>>iso_path<</>>iso_name<<' if >>local_only<< else '>>iso_url<<'`

---

### xenserver

**Builder type:** `xenserver-iso`

**Platform defs:**

| Variable | Value |
|----------|-------|
| `local` | `True` |

**Template variables referenced** (`>>var<<`):

- `cd_label` — spec
- `iso_checksum` — spec
- `iso_name` — spec
- `iso_path` — location
- `iso_url` — spec
- `local_only` — computed
- `name` — computed
- `vms_path` — location

**Value replacements** (`%>var<%`):

- `cd_files`

**Numeric expressions** (`#>expr<#`):

- `boot_disk_size`
- `cpu_sockets*cpu_cores`
- `memory`

**Eval expressions** (`E>expr<E`):

- `'' if >>local_only<< else '>>iso_path<</>>iso_name<<'`
- `'>>iso_checksum<<' if len('>>iso_checksum<<') else 'none'`
- `'>>iso_path<</>>iso_name<<' if >>local_only<< else '>>iso_url<<'`

---

## Enterprise Platforms

### vsphere

**Builder type:** `vsphere-iso`

**Platform defs:**

| Variable | Value |
|----------|-------|
| `thin_disk` | `False` |
| `vm_network` | `VM Network` |

**Template variables referenced** (`>>var<<`):

- `cd_label` — spec
- `cluster` — location
- `datacenter` — location
- `datastore` — location
- `esxi_host` — location
- `firmware` — computed
- `folder` — location
- `iso_checksum` — spec
- `iso_name` — spec
- `iso_path` — location
- `iso_url` — spec
- `local_only` — computed
- `location_name` — computed
- `name` — computed
- `spec_name` — spec
- `vm_network` — location

**Value replacements** (`%>var<%`):

- `cd_files`
- `thin_disk`

**Numeric expressions** (`#>expr<#`):

- `boot_disk_size`
- `cpu_sockets*cpu_cores`
- `memory`

**Eval expressions** (`E>expr<E`):

- `'>>iso_checksum<<' if len('>>iso_checksum<<') else 'none'`
- `'>>iso_path<</>>iso_name<<' if >>local_only<< else '>>iso_url<<'`
- `'windows' if '>>spec_name<<'.startswith('win') else 'linux'`

**Vault/credential variables:**

| Variable | Vault Path |
|----------|-----------|
| `vsphere-password` | `vsphere/>>location_name<<:password` |
| `vsphere-server` | `vsphere/>>location_name<<:server` |
| `vsphere-username` | `vsphere/>>location_name<<:username` |

---

### proxmox

**Builder type:** `proxmox-iso`

**Platform defs:**

| Variable | Value |
|----------|-------|
| `shutcmd` | `False` |

**Template variables referenced** (`>>var<<`):

- `boot_disk_size` — all.json default
- `cd_label` — spec
- `iso_checksum` — spec
- `iso_name` — spec
- `iso_path` — location
- `iso_storage_pool` — location
- `iso_url` — spec
- `local_only` — computed
- `location_name` — computed
- `name` — computed
- `proxmox_node` — location
- `vm_storage_pool` — location

**Value replacements** (`%>var<%`):

- `cd_files`

**Numeric expressions** (`#>expr<#`):

- `cpu_cores`
- `cpu_sockets`
- `memory`

**Eval expressions** (`E>expr<E`):

- `'' if >>local_only<< else '>>iso_path<</>>iso_name<<'`
- `'>>iso_checksum<<' if len('>>iso_checksum<<') else 'none'`
- `'false' if >>local_only<< else 'true'`
- `'local:iso/>>iso_name<<' if >>local_only<< else '>>iso_url<<'`

**Vault/credential variables:**

| Variable | Vault Path |
|----------|-----------|
| `name` | `{{ build_name }}` |
| `proxmox-password` | `proxmox/>>location_name<<:password` |
| `proxmox-server` | `proxmox/>>location_name<<:server` |
| `proxmox-username` | `proxmox/>>location_name<<:username` |

---

## Cloud Platforms

### azure

**Builder type:** `azure-arm`

**Platform defs:**

| Variable | Value |
|----------|-------|
| `boot` | `False` |
| `image_version` | `latest` |
| `shutcmd` | `False` |
| `vm_size` | `Standard_D2s_v3` |

**Template variables referenced** (`>>var<<`):

- `azure_image_offer` — spec
- `azure_image_publisher` — spec
- `azure_image_sku` — spec
- `azure_location` — location
- `azure_resource_group` — location
- `image_version` — computed
- `location_name` — computed
- `name` — computed
- `spec_name` — spec
- `vm_size` — computed

**Value replacements** (`%>var<%`):

- `azure_replication_regions`

**Eval expressions** (`E>expr<E`):

- `'Windows' if '>>spec_name<<'.startswith('win') else 'Linux'`

**Vault/credential variables:**

| Variable | Vault Path |
|----------|-----------|
| `az-bastion-hostname` | `azure/>>location_name<<:bastion_hostname` |
| `az-bastion-keyfile` | `azure/>>location_name<<:bastion_keyfile` |
| `az-bastion-username` | `azure/>>location_name<<:bastion_username` |
| `client-id` | `azure/>>location_name<<:client_id` |
| `client-secret` | `azure/>>location_name<<:client_secret` |
| `gallery-name` | `azure/>>location_name<<:gallery_name` |
| `gallery-resource-group` | `azure/>>location_name<<:gallery_resource_group` |
| `gallery-subscription-id` | `azure/>>location_name<<:gallery_subscription_id` |
| `subscription-id` | `azure/>>location_name<<:subscription_id` |
| `tenant-id` | `azure/>>location_name<<:tenant_id` |

---

### gcp

**Builder type:** `googlecompute`

**Platform defs:**

| Variable | Value |
|----------|-------|
| `boot` | `False` |
| `disk_type` | `pd-ssd` |
| `machine_type` | `n1-standard-2` |
| `shutcmd` | `False` |
| `state_timeout` | `15m` |

**Template variables referenced** (`>>var<<`):

- `disk_type` — computed
- `gcp_image_family` — spec
- `gcp_region` — location
- `gcp_source_image_family` — spec
- `gcp_source_image_project_id` — spec
- `gcp_zone` — location
- `location_name` — computed
- `machine_type` — computed
- `name` — computed
- `state_timeout` — computed

**Vault/credential variables:**

| Variable | Vault Path |
|----------|-----------|
| `gcp-bastion-hostname` | `gcp/>>location_name<<:bastion_hostname` |
| `gcp-bastion-password` | `gcp/>>location_name<<:bastion_password` |
| `gcp-bastion-username` | `gcp/>>location_name<<:bastion_username` |
| `gcp-creds` | `gcp/>>location_name<<:credentials_json` |
| `project-id` | `gcp/>>location_name<<:project_id` |
| `service-account-email` | `gcp/>>location_name<<:service_account_email` |

---

### aws

**Builder type:** `amazon-ebs`

**Platform defs:**

| Variable | Value |
|----------|-------|
| `boot` | `False` |
| `instance_type` | `t3.medium` |
| `shutcmd` | `False` |

**Template variables referenced** (`>>var<<`):

- `aws_ami_filter_name` — spec
- `aws_region` — location
- `aws_subnet_id` — location
- `aws_vpc_id` — location
- `instance_type` — computed
- `location_name` — computed
- `name` — computed

**Value replacements** (`%>var<%`):

- `aws_ami_owners`

**Vault/credential variables:**

| Variable | Vault Path |
|----------|-----------|
| `aws-access-key` | `aws/>>location_name<<:access_key` |
| `aws-secret-key` | `aws/>>location_name<<:secret_key` |

---

## Special Platforms

### none

**Builder type:** `null`

**Platform defs:**

| Variable | Value |
|----------|-------|
| `boot` | `False` |
| `shutcmd` | `False` |

---

## Computed Defs

These defs are computed during the build pipeline and are available for template substitution:

| Variable | Source | Description |
|----------|--------|-------------|
| `name` | CLI or spec | VM/image name (hostname or spec name) |
| `fqdn` | Computed | Fully qualified domain name (name + domain) |
| `ip` | CLI or DNS | IP address (from CLI arg or DNS lookup) |
| `platform` | CLI | Platform name from target |
| `location` | CLI | Location name from target |
| `dist` | Spec provides | Distribution name |
| `version` | Spec provides | Full version string |
| `major` | Computed | Major version number |
| `minor` | Computed | Minor version number |
| `arch` | Spec provides | Architecture (x86_64, aarch64, etc.) |
| `firmware` | Location or default | Firmware type (bios or efi) |
| `base_path` | Settings | OSImager package base directory |
| `data_path` | Settings | Data directory path |
| `user_dir` | Settings | User config directory (~/.config/osimager) |
| `temp_dir` | Computed | Temporary build directory |
| `spec_dir` | Computed | Spec data directory path |
| `spec_name` | Computed | Spec identifier (dist-version-arch) |
| `platform_name` | CLI | Platform name |
| `location_name` | CLI | Location name |
| `platform_type` | Platform config | Packer builder type |
| `subnet` | Computed | Subnet from CIDR |
| `prefix` | Computed | Network prefix from CIDR |
| `netmask` | Computed | Netmask from CIDR prefix |
| `gateway` | Location or CIDR | Gateway address |
| `dns1` | Location DNS | Primary DNS server |
| `dns2` | Location DNS | Secondary DNS server |
| `dns_search` | Location DNS | DNS search domain |
| `ntp1` | Location NTP | Primary NTP server |
| `iso_url` | Spec or local | ISO download URL |
| `iso_name` | Computed | ISO filename |
| `iso_checksum` | Computed | ISO checksum value |
| `local_only` | Settings | Whether to use local ISOs only |
