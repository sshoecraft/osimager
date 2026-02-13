# Supported Operating Systems

This page is auto-generated from the spec data files.

## Summary

| Metric | Count |
|--------|-------|
| Distributions | 11 |
| Total versions | 258 |
| Total specs (version x arch) | 701 |

## Overview

| Distribution | Versions | Architectures | Installer | Cloud |
|-------------|----------|---------------|-----------|-------|
| Red Hat Enterprise Linux | 2.1 - 10.1 | i386, x86_64, aarch64 | kickstart | Azure, GCP, AWS |
| AlmaLinux | 8.3 - 10.1 | x86_64, aarch64 | kickstart | Azure, GCP, AWS |
| Rocky Linux | 8.3 - 10.1 | x86_64, aarch64 | kickstart | Azure, GCP, AWS |
| CentOS | 5.0 - 8.5 | i386, x86_64, aarch64 | kickstart | Azure, GCP, AWS |
| Oracle Enterprise Linux | 5.0 - 10.1 | i386, x86_64, aarch64 | kickstart | Azure, GCP, AWS |
| Debian | 8.0 - 13.3 | i386, x86_64, aarch64 | preseed | Azure, GCP, AWS |
| Ubuntu | 18.04 - 24.04 | x86_64, aarch64 | cloud-init | Azure, GCP, AWS |
| SUSE Linux Enterprise Server | 12.1 - 16.0 | x86_64, aarch64 | autoyast | Azure, GCP, AWS |
| VMware ESXi | 5.5U3 - 8.0U2 | x86_64 | kickstart | - |
| System V Release 4 | 2.1 | i386 | none | - |
| Windows Server | 2016 - 2025 | x86_64 | autounattend | Azure, GCP, AWS |

## Distribution Details

### Red Hat Enterprise Linux

**Spec name:** `rhel`

**Include chain:** rhel → linux → ssh

**Installer type:** kickstart

**Version ranges:** `2.1, 3.0, 4.8, 5.[1,9,10,11], 6.[9-10], 7.[5-9], 8.[0,1,2,3,5,6,7,8,9,10], 9.[0-7], 10.[0-1]`

**Versions (34):** 2.1, 3.0, 4.8, 5.1, 5.9, 5.10, 5.11, 6.9, 6.10, 7.5, 7.6, 7.7, 7.8, 7.9, 8.0, 8.1, 8.2, 8.3, 8.5, 8.6, 8.7, 8.8, 8.9, 8.10, 9.0, 9.1, 9.2, 9.3, 9.4, 9.5, 9.6, 9.7, 10.0, 10.1

**Architectures:** i386, x86_64, aarch64

**Platforms:** Local: virtualbox, vmware, qemu, libvirt, xenserver, hyperv | Enterprise: vsphere, proxmox | Cloud: azure, gcp, aws | Other: none

**Cloud image support:**

- **AZURE**: version patterns 10.*, 7.*, 8.*, 9.*
- **GCP**: version patterns 10.*, 7.*, 8.*, 9.*
- **AWS**: version patterns 10.*, 7.*, 8.*, 9.*

**Spec count:** 102

---

### AlmaLinux

**Spec name:** `alma`

**Include chain:** alma → rhel → linux → ssh

**Installer type:** kickstart

**Version ranges:** `8.[3-10], 9.[0-7], 10.[0-1]`

**Versions (18):** 8.3, 8.4, 8.5, 8.6, 8.7, 8.8, 8.9, 8.10, 9.0, 9.1, 9.2, 9.3, 9.4, 9.5, 9.6, 9.7, 10.0, 10.1

**Architectures:** x86_64, aarch64

**Platforms:** Local: virtualbox, vmware, qemu, libvirt, xenserver, hyperv | Enterprise: vsphere, proxmox | Cloud: azure, gcp, aws | Other: none

**Cloud image support:**

- **AZURE**: version patterns 10.*, 8.*, 9.*
- **GCP**: version patterns 10.*, 8.*, 9.*
- **AWS**: version patterns 10.*, 8.*, 9.*

**Spec count:** 36

---

### Rocky Linux

**Spec name:** `rocky`

**Include chain:** rocky → rhel → linux → ssh

**Installer type:** kickstart

**Version ranges:** `8.[3-9], 9.[0-7], 10.[0-1]`

**Versions (17):** 8.3, 8.4, 8.5, 8.6, 8.7, 8.8, 8.9, 9.0, 9.1, 9.2, 9.3, 9.4, 9.5, 9.6, 9.7, 10.0, 10.1

**Architectures:** x86_64, aarch64

**Platforms:** Local: virtualbox, vmware, qemu, libvirt, xenserver, hyperv | Enterprise: vsphere, proxmox | Cloud: azure, gcp, aws | Other: none

**Cloud image support:**

- **AZURE**: version patterns 10.*, 8.*, 9.*
- **GCP**: version patterns 10.*, 8.*, 9.*
- **AWS**: version patterns 10.*, 8.*, 9.*

**Spec count:** 34

---

### CentOS

**Spec name:** `centos`

**Include chain:** centos → rhel → linux → ssh

**Installer type:** kickstart

**Version ranges:** `5.[0-10], 6.[0-10], 7.[0-9], 8.[0-5]`

**Versions (38):** 5.0, 5.1, 5.2, 5.3, 5.4, 5.5, 5.6, 5.7, 5.8, 5.9, 5.10, 6.0, 6.1, 6.2, 6.3, 6.4, 6.5, 6.6, 6.7, 6.8, 6.9, 6.10, 7.0, 7.1, 7.2, 7.3, 7.4, 7.5, 7.6, 7.7, 7.8, 7.9, 8.0, 8.1, 8.2, 8.3, 8.4, 8.5

**Architectures:** i386, x86_64, aarch64

**Platforms:** Local: virtualbox, vmware, qemu, libvirt, xenserver, hyperv | Enterprise: vsphere, proxmox | Cloud: azure, gcp, aws | Other: none

**Cloud image support:**

- **AZURE**: version patterns 7.*, 8.*
- **GCP**: version patterns 7.*, 8.*
- **AWS**: version patterns 7.*, 8.*

**Spec count:** 114

---

### Oracle Enterprise Linux

**Spec name:** `oel`

**Include chain:** oel → rhel → linux → ssh

**Installer type:** kickstart

**Version ranges:** `5.[0-10], 6.[0-10], 7.[0-9], 8.[0-10], 9.[0-7], 10.[0-1]`

**Versions (53):** 5.0, 5.1, 5.2, 5.3, 5.4, 5.5, 5.6, 5.7, 5.8, 5.9, 5.10, 6.0, 6.1, 6.2, 6.3, 6.4, 6.5, 6.6, 6.7, 6.8, 6.9, 6.10, 7.0, 7.1, 7.2, 7.3, 7.4, 7.5, 7.6, 7.7, 7.8, 7.9, 8.0, 8.1, 8.2, 8.3, 8.4, 8.5, 8.6, 8.7, 8.8, 8.9, 8.10, 9.0, 9.1, 9.2, 9.3, 9.4, 9.5, 9.6, 9.7, 10.0, 10.1

**Architectures:** i386, x86_64, aarch64

**Platforms:** Local: virtualbox, vmware, qemu, libvirt, xenserver, hyperv | Enterprise: vsphere, proxmox | Cloud: azure, gcp, aws | Other: none

**Cloud image support:**

- **AZURE**: version patterns 10.*, 7.*, 8.*, 9.*
- **GCP**: version patterns 10.*, 7.*, 8.*, 9.*
- **AWS**: version patterns 10.*, 7.*, 8.*, 9.*

**Spec count:** 159

---

### Debian

**Spec name:** `debian`

**Include chain:** debian → linux → ssh

**Installer type:** preseed

**Version ranges:** `8.[0-11], 9.[0-13], 10.[0-13], 11.[0-11], 12.[0-13], 13.[0-3]`

**Versions (70):** 8.0, 8.1, 8.2, 8.3, 8.4, 8.5, 8.6, 8.7, 8.8, 8.9, 8.10, 8.11, 9.0, 9.1, 9.2, 9.3, 9.4, 9.5, 9.6, 9.7, 9.8, 9.9, 9.10, 9.11, 9.12, 9.13, 10.0, 10.1, 10.2, 10.3, 10.4, 10.5, 10.6, 10.7, 10.8, 10.9, 10.10, 10.11, 10.12, 10.13, 11.0, 11.1, 11.2, 11.3, 11.4, 11.5, 11.6, 11.7, 11.8, 11.9, 11.10, 11.11, 12.0, 12.1, 12.2, 12.3, 12.4, 12.5, 12.6, 12.7, 12.8, 12.9, 12.10, 12.11, 12.12, 12.13, 13.0, 13.1, 13.2, 13.3

**Architectures:** i386, x86_64, aarch64

**Platforms:** Local: virtualbox, vmware, qemu, libvirt, xenserver, hyperv | Enterprise: vsphere, proxmox | Cloud: azure, gcp, aws | Other: none

**Cloud image support:**

- **AZURE**: version patterns 11.*, 12.*
- **GCP**: version patterns 11.*, 12.*
- **AWS**: version patterns 11.*, 12.*

**Spec count:** 210

---

### Ubuntu

**Spec name:** `ubuntu`

**Include chain:** ubuntu → linux → ssh

**Installer type:** cloud-init

**Version ranges:** `18.04, 20.04, 22.04, 24.04`

**Versions (4):** 18.04, 20.04, 22.04, 24.04

**Architectures:** x86_64, aarch64

**Platforms:** Local: virtualbox, vmware, qemu, libvirt, xenserver, hyperv | Enterprise: vsphere, proxmox | Cloud: azure, gcp, aws | Other: none

**Cloud image support:**

- **AZURE**: version patterns 20.04, 22.04, 24.04
- **GCP**: version patterns 20.04, 22.04, 24.04
- **AWS**: version patterns 20.04, 22.04, 24.04

**Spec count:** 8

---

### SUSE Linux Enterprise Server

**Spec name:** `sles`

**Include chain:** sles → linux → ssh

**Installer type:** autoyast

**Version ranges:** `12.[1-5], 15.[0-7], 16.[0-0]`

**Versions (14):** 12.1, 12.2, 12.3, 12.4, 12.5, 15.0, 15.1, 15.2, 15.3, 15.4, 15.5, 15.6, 15.7, 16.0

**Architectures:** x86_64, aarch64

**Platforms:** Local: virtualbox, vmware, qemu, libvirt, xenserver, hyperv | Enterprise: vsphere, proxmox | Cloud: azure, gcp, aws | Other: none

**Cloud image support:**

- **AZURE**: version patterns 15.*
- **GCP**: version patterns 15.*
- **AWS**: version patterns 15.*

**Spec count:** 28

---

### VMware ESXi

**Spec name:** `esxi`

**Installer type:** kickstart

**Version ranges:** `5.5U3, 6.0U2, 6.5, 7.0U3n, 8.0U2`

**Versions (5):** 5.5U3, 6.0U2, 6.5, 7.0U3n, 8.0U2

**Architectures:** x86_64

**Platforms:** Local: vmware | Enterprise: vsphere

**Spec count:** 5

---

### System V Release 4

**Spec name:** `sysvr4`

**Installer type:** none

**Version ranges:** `2.1`

**Versions (1):** 2.1

**Architectures:** i386

**Platforms:** Local: virtualbox, vmware | Enterprise: proxmox

**Spec count:** 1

---

### Windows Server

**Spec name:** `windows-server`

**Include chain:** windows-server → windows → winrm

**Installer type:** autounattend

**Version ranges:** `2016, 2019, 2022, 2025`

**Versions (4):** 2016, 2019, 2022, 2025

**Architectures:** x86_64

**Platforms:** Local: virtualbox, vmware, xenserver, hyperv | Enterprise: vsphere, proxmox | Cloud: azure, gcp, aws | Other: none

**Cloud image support:**

- **AZURE**: version patterns 2016, 2019, 2022, 2025
- **GCP**: version patterns 2016, 2019, 2022, 2025
- **AWS**: version patterns 2016, 2019, 2022, 2025

**Spec count:** 4

---
