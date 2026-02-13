# Installation

## Quick Install

```bash
pip install osimager
```

## Prerequisites

- **Python 3.8+**
- **HashiCorp Packer** -- [install instructions](https://developer.hashicorp.com/packer/install)
- **Ansible** -- `pip install ansible`
- **A hypervisor** -- VirtualBox is free and easiest to start with
- **mkisofs** -- `brew install cdrtools` (macOS) or `apt install genisoimage` (Linux)

## Packer Plugins

OSImager supports 13 platforms. Each requires its corresponding Packer plugin:

| Platform | Builder Type | Plugin Install |
|----------|-------------|----------------|
| VirtualBox | virtualbox-iso | `packer plugins install github.com/hashicorp/virtualbox` |
| VMware | vmware-iso | `packer plugins install github.com/hashicorp/vmware` |
| vSphere | vsphere-iso | `packer plugins install github.com/hashicorp/vsphere` |
| Proxmox | proxmox-iso | `packer plugins install github.com/hashicorp/proxmox` |
| QEMU/KVM | qemu | `packer plugins install github.com/hashicorp/qemu` |
| libvirt | qemu (libvirt) | `packer plugins install github.com/thomasklein94/libvirt` |
| Hyper-V | hyperv-iso | Built-in (no plugin needed) |
| XenServer | xenserver-iso | `packer plugins install github.com/ddelnano/xenserver` |
| Azure | azure-arm | `packer plugins install github.com/hashicorp/azure` |
| GCP | googlecompute | `packer plugins install github.com/hashicorp/googlecompute` |
| AWS | amazon-ebs | `packer plugins install github.com/hashicorp/amazon` |
| none | null | Built-in |

The Ansible provisioner plugin is required for all platforms:

```bash
packer plugins install github.com/hashicorp/ansible
```

You only need to install plugins for the platforms you intend to use.

## Verification

```bash
mkosimage --version
```
