# Supported Operating Systems

This page is auto-generated from the spec data files.

## Summary

| Metric | Count |
|--------|-------|
| Distributions | 40 |
| Total versions | 392 |
| Total specs (version x arch) | 703 |

## Overview

| Distribution | Versions | Architectures | Installer | Cloud |
|-------------|----------|---------------|-----------|-------|
| Red Hat Enterprise Linux | 2.1 - 10.1 | x86_64, aarch64, i386 | kickstart | Azure, GCP, AWS |
| AlmaLinux | 8.3 - 10.2 | x86_64, aarch64 | kickstart | Azure, GCP, AWS |
| Rocky Linux | 8.3 - 9.8 | x86_64, aarch64 | kickstart | Azure, GCP, AWS |
| CentOS | 2.1 - 10 | x86_64, aarch64, i386 | kickstart | Azure, GCP, AWS |
| Oracle Enterprise Linux | 5.0 - 10.2 | x86_64, aarch64, i386 | kickstart | Azure, GCP, AWS |
| Debian | 8.0 - 13.7 | x86_64, aarch64, i386 | preseed | Azure, GCP, AWS |
| Ubuntu | 18.04 - 26.04.1 | x86_64, aarch64 | cloud-init | Azure, GCP, AWS |
| SUSE Linux Enterprise Server | 12.1 - 16.0 | x86_64, aarch64 | autoyast | Azure, GCP, AWS |
| VMware ESXi | 5.5U3 - 8.0U2 | x86_64 | kickstart | - |
| System V Release 4 | 2.1 | i386 | none | - |
| Windows Server | 2016 - 2025 | x86_64 | autounattend | Azure, GCP, AWS |
| Alpine Linux | 3.21 - 3.24 | x86_64, aarch64, i386 | alpine-answerfile | - |
| Amazon Linux | 2 - 2023 | x86_64, aarch64 | none | AWS |
| Arch Linux | rolling | x86_64 | archinstall | - |
| dragonfly | 6.4 - 6.4.2 | x86_64 | none | - |
| VMware ESX | 4.1U3 | x86_64 | kickstart | - |
| VMware ESXi 3.5 | 3.5U5 | i386 | kickstart | - |
| Fedora | 7 - 44 | x86_64, aarch64, i386 | kickstart | GCP, AWS |
| fedora-coreos | stable | x86_64, aarch64 | ignition | - |
| Flatcar Container Linux | stable | x86_64 | ignition | - |
| FreeBSD | 14.4 - 15.1 | x86_64 | none | - |
| Linux Mint | 22.2 - 22.3 | x86_64 | preseed | - |
| MX Linux | 23.5 - 23.6 | x86_64 | none | - |
| netbsd | 10.1 - 10.2 | x86_64, aarch64, i386 | none | - |
| omnios | r151052 | x86_64 | none | - |
| OpenBSD | 7.6 - 7.9 | x86_64, aarch64, i386 | openbsd-autoinstall | - |
| openindiana | hipster | x86_64 | none | - |
| openSUSE Leap | 15.6 - 16.0 | x86_64, aarch64 | autoyast | - |
| openwrt | 24.10 | x86_64, aarch64 | none | - |
| OPNsense | 25.7 | x86_64 | none | - |
| pfSense | 2.7.2 | x86_64 | none | - |
| VMware Photon OS | 5.0 | x86_64, aarch64 | photon-kickstart | - |
| Proxmox VE | 3.4 - 9.2 | x86_64 | answer.toml | - |
| SCO OpenServer | 5.0.5 | i386 | none | - |
| solaris | 11.4 | x86_64 | none | - |
| TrueNAS | 25.10 | x86_64 | none | - |
| UnixWare | 7.1 | i386 | none | - |
| VyOS | 1.4 | x86_64 | none | - |
| windows-desktop | 10 - 11 | x86_64 | autounattend | - |
| XCP-ng | 8.2.1 - 8.3 | x86_64 | answerfile.xml | - |

## Distribution Details

### Red Hat Enterprise Linux

**Spec name:** `rhel`

**Include chain:** rhel → linux → ssh

**Installer type:** kickstart

**Version ranges:** `2.1, 3.0, 4.8, 5.[1,9,10,11], 6.[0,9,10], 7.[5-9], 8.[0,1,2,3,5,6,7,8,9,10], 9.[0-8], 10.[0-1]`

**Versions (36):** 2.1, 3.0, 4.8, 5.1, 5.9, 5.10, 5.11, 6.0, 6.9, 6.10, 7.5, 7.6, 7.7, 7.8, 7.9, 8.0, 8.1, 8.2, 8.3, 8.5, 8.6, 8.7, 8.8, 8.9, 8.10, 9.0, 9.1, 9.2, 9.3, 9.4, 9.5, 9.6, 9.7, 9.8, 10.0, 10.1

**Architectures:** x86_64, aarch64, i386

**Platforms:** Local: virtualbox, vmware, qemu, xenserver, hyperv | Enterprise: vsphere, proxmox | Cloud: azure, gcp, aws | Other: none

**Cloud image support:**

- **AZURE**: version patterns 10.*, 7.*, 8.*, 9.*
- **GCP**: version patterns 10.*, 7.*, 8.*, 9.*
- **AWS**: version patterns 10.*, 7.*, 8.*, 9.*

**Spec count:** 57

---

### AlmaLinux

**Spec name:** `alma`

**Include chain:** alma → rhel → linux → ssh

**Installer type:** kickstart

**Version ranges:** `8.[3-10], 9.[0-8], 10.[0-2]`

**Versions (20):** 8.3, 8.4, 8.5, 8.6, 8.7, 8.8, 8.9, 8.10, 9.0, 9.1, 9.2, 9.3, 9.4, 9.5, 9.6, 9.7, 9.8, 10.0, 10.1, 10.2

**Architectures:** x86_64, aarch64

**Platforms:** Local: virtualbox, vmware, qemu, xenserver, hyperv | Enterprise: vsphere, proxmox | Cloud: azure, gcp, aws | Other: none

**Cloud image support:**

- **AZURE**: version patterns 10.*, 8.*, 9.*
- **GCP**: version patterns 10.*, 8.*, 9.*
- **AWS**: version patterns 10.*, 8.*, 9.*

**Spec count:** 40

---

### Rocky Linux

**Spec name:** `rocky`

**Include chain:** rocky → rhel → linux → ssh

**Installer type:** kickstart

**Version ranges:** `8.[3-10], 9.[0-8]`

**Versions (17):** 8.3, 8.4, 8.5, 8.6, 8.7, 8.8, 8.9, 8.10, 9.0, 9.1, 9.2, 9.3, 9.4, 9.5, 9.6, 9.7, 9.8

**Architectures:** x86_64, aarch64

**Platforms:** Local: virtualbox, vmware, qemu, xenserver, hyperv | Enterprise: vsphere, proxmox | Cloud: azure, gcp, aws | Other: none

**Cloud image support:**

- **AZURE**: version patterns 8.*, 9.*
- **GCP**: version patterns 8.*, 9.*
- **AWS**: version patterns 8.*, 9.*

**Spec count:** 34

---

### CentOS

**Spec name:** `centos`

**Include chain:** centos → rhel → linux → ssh

**Installer type:** kickstart

**Version ranges:** `2.1, 3.[0-9], 4.[0-8], 5.[0-10], 6.[0-10], 7.[0-9], 8.[0-5], 9, 10`

**Versions (60):** 2.1, 3.0, 3.1, 3.2, 3.3, 3.4, 3.5, 3.6, 3.7, 3.8, 3.9, 4.0, 4.1, 4.2, 4.3, 4.4, 4.5, 4.6, 4.7, 4.8, 5.0, 5.1, 5.2, 5.3, 5.4, 5.5, 5.6, 5.7, 5.8, 5.9, 5.10, 6.0, 6.1, 6.2, 6.3, 6.4, 6.5, 6.6, 6.7, 6.8, 6.9, 6.10, 7.0, 7.1, 7.2, 7.3, 7.4, 7.5, 7.6, 7.7, 7.8, 7.9, 8.0, 8.1, 8.2, 8.3, 8.4, 8.5, 9, 10

**Architectures:** x86_64, aarch64, i386

**Platforms:** Local: virtualbox, vmware, qemu, xenserver, hyperv | Enterprise: vsphere, proxmox | Cloud: azure, gcp, aws | Other: none

**Cloud image support:**

- **AZURE**: version patterns 10, 7.*, 8.*, 9
- **GCP**: version patterns 10, 7.*, 8.*, 9
- **AWS**: version patterns 10, 7.*, 8.*, 9

**Spec count:** 109

---

### Oracle Enterprise Linux

**Spec name:** `oel`

**Include chain:** oel → rhel → linux → ssh

**Installer type:** kickstart

**Version ranges:** `5.[0-10], 6.[0-10], 7.[0-9], 8.[0-10], 9.[0-8], 10.[0-2]`

**Versions (55):** 5.0, 5.1, 5.2, 5.3, 5.4, 5.5, 5.6, 5.7, 5.8, 5.9, 5.10, 6.0, 6.1, 6.2, 6.3, 6.4, 6.5, 6.6, 6.7, 6.8, 6.9, 6.10, 7.0, 7.1, 7.2, 7.3, 7.4, 7.5, 7.6, 7.7, 7.8, 7.9, 8.0, 8.1, 8.2, 8.3, 8.4, 8.5, 8.6, 8.7, 8.8, 8.9, 8.10, 9.0, 9.1, 9.2, 9.3, 9.4, 9.5, 9.6, 9.7, 9.8, 10.0, 10.1, 10.2

**Architectures:** x86_64, aarch64, i386

**Platforms:** Local: virtualbox, vmware, qemu, xenserver, hyperv | Enterprise: vsphere, proxmox | Cloud: azure, gcp, aws | Other: none

**Cloud image support:**

- **AZURE**: version patterns 10.*, 7.*, 8.*, 9.*
- **GCP**: version patterns 10.*, 7.*, 8.*, 9.*
- **AWS**: version patterns 10.*, 7.*, 8.*, 9.*

**Spec count:** 98

---

### Debian

**Spec name:** `debian`

**Include chain:** debian → linux → ssh

**Installer type:** preseed

**Version ranges:** `8.[0-11], 9.[0-13], 10.[0-13], 11.[0-11], 12.[0-15], 13.[0-7]`

**Versions (76):** 8.0, 8.1, 8.2, 8.3, 8.4, 8.5, 8.6, 8.7, 8.8, 8.9, 8.10, 8.11, 9.0, 9.1, 9.2, 9.3, 9.4, 9.5, 9.6, 9.7, 9.8, 9.9, 9.10, 9.11, 9.12, 9.13, 10.0, 10.1, 10.2, 10.3, 10.4, 10.5, 10.6, 10.7, 10.8, 10.9, 10.10, 10.11, 10.12, 10.13, 11.0, 11.1, 11.2, 11.3, 11.4, 11.5, 11.6, 11.7, 11.8, 11.9, 11.10, 11.11, 12.0, 12.1, 12.2, 12.3, 12.4, 12.5, 12.6, 12.7, 12.8, 12.9, 12.10, 12.11, 12.12, 12.13, 12.14, 12.15, 13.0, 13.1, 13.2, 13.3, 13.4, 13.5, 13.6, 13.7

**Architectures:** x86_64, aarch64, i386

**Platforms:** Local: virtualbox, vmware, qemu, xenserver, hyperv | Enterprise: vsphere, proxmox | Cloud: azure, gcp, aws | Other: none

**Cloud image support:**

- **AZURE**: version patterns 11.*, 12.*, 13.*
- **GCP**: version patterns 11.*, 12.*, 13.*
- **AWS**: version patterns 11.*, 12.*, 13.*

**Spec count:** 152

---

### Ubuntu

**Spec name:** `ubuntu`

**Include chain:** ubuntu → linux → ssh

**Installer type:** cloud-init

**Version ranges:** `18.04, 20.04, 22.04, 24.04.[2-5], 25.10, 26.04, 26.04.1`

**Versions (10):** 18.04, 20.04, 22.04, 24.04.2, 24.04.3, 24.04.4, 24.04.5, 25.10, 26.04, 26.04.1

**Architectures:** x86_64, aarch64

**Platforms:** Local: virtualbox, vmware, qemu, xenserver, hyperv | Enterprise: vsphere, proxmox | Cloud: azure, gcp, aws | Other: none

**Cloud image support:**

- **AZURE**: version patterns 20.04, 22.04, 24.04.*, 26.04.*
- **GCP**: version patterns 20.04, 22.04, 24.04.*, 26.04.*
- **AWS**: version patterns 20.04, 22.04, 24.04.*, 26.04.*

**Spec count:** 19

---

### SUSE Linux Enterprise Server

**Spec name:** `sles`

**Include chain:** sles → linux → ssh

**Installer type:** autoyast

**Version ranges:** `12.[1-5], 15.[0-7], 16.[0-0]`

**Versions (14):** 12.1, 12.2, 12.3, 12.4, 12.5, 15.0, 15.1, 15.2, 15.3, 15.4, 15.5, 15.6, 15.7, 16.0

**Architectures:** x86_64, aarch64

**Platforms:** Local: virtualbox, vmware, qemu, xenserver, hyperv | Enterprise: vsphere, proxmox | Cloud: azure, gcp, aws | Other: none

**Cloud image support:**

- **AZURE**: version patterns 15.*
- **GCP**: version patterns 15.*
- **AWS**: version patterns 15.*

**Spec count:** 23

---

### VMware ESXi

**Spec name:** `esxi`

**Installer type:** kickstart

**Version ranges:** `5.5U3, 6.0U2, 6.5, 7.0, 7.0U1c, 7.0U3d, 7.0U3n, 8.0U2`

**Versions (8):** 5.5U3, 6.0U2, 6.5, 7.0, 7.0U1c, 7.0U3d, 7.0U3n, 8.0U2

**Architectures:** x86_64

**Platforms:** Local: vmware | Enterprise: vsphere

**Spec count:** 8

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

### Alpine Linux

**Spec name:** `alpine`

**Include chain:** alpine → ssh

**Installer type:** alpine-answerfile

**Version ranges:** `3.21, 3.22, 3.23, 3.24`

**Versions (4):** 3.21, 3.22, 3.23, 3.24

**Architectures:** x86_64, aarch64, i386

**Platforms:** Local: virtualbox, vmware, qemu, hyperv | Enterprise: vsphere, proxmox | Other: none

**Spec count:** 12

---

### Amazon Linux

**Spec name:** `amazon`

**Include chain:** amazon → linux → ssh

**Installer type:** none

**Version ranges:** `2, 2023`

**Versions (2):** 2, 2023

**Architectures:** x86_64, aarch64

**Platforms:** Local: qemu, vmware | Enterprise: proxmox | Cloud: aws | Other: none

**Cloud image support:**

- **AWS**: version patterns 2, 2023

**Spec count:** 3

---

### Arch Linux

**Spec name:** `arch`

**Include chain:** arch → ssh

**Installer type:** archinstall

**Version ranges:** `rolling`

**Versions (1):** rolling

**Architectures:** x86_64

**Platforms:** Local: virtualbox, vmware, qemu, hyperv | Enterprise: vsphere, proxmox | Other: none

**Spec count:** 1

---

### dragonfly

**Spec name:** `dragonfly`

**Include chain:** dragonfly → ssh

**Installer type:** none

**Version ranges:** `6.4, 6.4.2`

**Versions (2):** 6.4, 6.4.2

**Architectures:** x86_64

**Platforms:** Local: qemu, vmware, virtualbox | Other: none

**Spec count:** 2

---

### VMware ESX

**Spec name:** `esx`

**Installer type:** kickstart

**Version ranges:** `4.1U3`

**Versions (1):** 4.1U3

**Architectures:** x86_64

**Platforms:** Local: vmware | Enterprise: vsphere

**Spec count:** 1

---

### VMware ESXi 3.5

**Spec name:** `esxi35`

**Installer type:** kickstart

**Version ranges:** `3.5U5`

**Versions (1):** 3.5U5

**Architectures:** i386

**Platforms:** Local: vmware | Enterprise: vsphere

**Spec count:** 1

---

### Fedora

**Spec name:** `fedora`

**Include chain:** fedora → linux → ssh

**Installer type:** kickstart

**Version ranges:** `[7-44]`

**Versions (38):** 7, 8, 9, 10, 11, 12, 13, 14, 15, 16, 17, 18, 19, 20, 21, 22, 23, 24, 25, 26, 27, 28, 29, 30, 31, 32, 33, 34, 35, 36, 37, 38, 39, 40, 41, 42, 43, 44

**Architectures:** x86_64, aarch64, i386

**Platforms:** Local: virtualbox, vmware, qemu, hyperv | Enterprise: vsphere, proxmox | Cloud: azure, gcp, aws | Other: none

**Cloud image support:**

- **GCP**: version patterns 44, 4[34]
- **AWS**: version patterns 44, 4[34]

**Spec count:** 79

---

### fedora-coreos

**Spec name:** `fedora-coreos`

**Include chain:** fedora-coreos → ssh

**Installer type:** ignition

**Version ranges:** `stable`

**Versions (1):** stable

**Architectures:** x86_64, aarch64

**Platforms:** Local: virtualbox, vmware, qemu | Enterprise: vsphere, proxmox | Other: none

**Spec count:** 2

---

### Flatcar Container Linux

**Spec name:** `flatcar`

**Include chain:** flatcar → ssh

**Installer type:** ignition

**Version ranges:** `stable`

**Versions (1):** stable

**Architectures:** x86_64

**Platforms:** Local: virtualbox, vmware, qemu | Enterprise: vsphere, proxmox | Other: none

**Spec count:** 1

---

### FreeBSD

**Spec name:** `freebsd`

**Include chain:** freebsd → ssh

**Installer type:** none

**Version ranges:** `14.[4-5], 15.[0-1]`

**Versions (4):** 14.4, 14.5, 15.0, 15.1

**Architectures:** x86_64

**Platforms:** Local: virtualbox, vmware, qemu, hyperv | Enterprise: vsphere, proxmox

**Spec count:** 4

---

### Linux Mint

**Spec name:** `mint`

**Include chain:** mint → linux → ssh

**Installer type:** preseed

**Version ranges:** `22.[2-3]`

**Versions (2):** 22.2, 22.3

**Architectures:** x86_64

**Platforms:** Local: virtualbox, vmware, qemu, hyperv | Enterprise: vsphere, proxmox | Other: none

**Spec count:** 2

---

### MX Linux

**Spec name:** `mxlinux`

**Include chain:** mxlinux → linux → ssh

**Installer type:** none

**Version ranges:** `23.5, 23.6`

**Versions (2):** 23.5, 23.6

**Architectures:** x86_64

**Platforms:** Local: virtualbox, vmware, qemu | Enterprise: proxmox | Other: none

**Spec count:** 2

---

### netbsd

**Spec name:** `netbsd`

**Include chain:** netbsd → ssh

**Installer type:** none

**Version ranges:** `10.[1-2]`

**Versions (2):** 10.1, 10.2

**Architectures:** x86_64, aarch64, i386

**Platforms:** Local: qemu, vmware, virtualbox | Other: none

**Spec count:** 6

---

### omnios

**Spec name:** `omnios`

**Include chain:** omnios → ssh

**Installer type:** none

**Version ranges:** `r151052`

**Versions (1):** r151052

**Architectures:** x86_64

**Platforms:** Local: qemu, vmware | Enterprise: proxmox | Other: none

**Spec count:** 1

---

### OpenBSD

**Spec name:** `openbsd`

**Include chain:** openbsd → ssh

**Installer type:** openbsd-autoinstall

**Version ranges:** `7.[6-9]`

**Versions (4):** 7.6, 7.7, 7.8, 7.9

**Architectures:** x86_64, aarch64, i386

**Platforms:** Local: virtualbox, vmware, qemu | Enterprise: vsphere, proxmox | Other: none

**Spec count:** 12

---

### openindiana

**Spec name:** `openindiana`

**Include chain:** openindiana → ssh

**Installer type:** none

**Version ranges:** `hipster`

**Versions (1):** hipster

**Architectures:** x86_64

**Platforms:** Local: qemu, vmware, virtualbox | Other: none

**Spec count:** 1

---

### openSUSE Leap

**Spec name:** `opensuse`

**Include chain:** opensuse → linux → ssh

**Installer type:** autoyast

**Version ranges:** `15.6, 16.0`

**Versions (2):** 15.6, 16.0

**Architectures:** x86_64, aarch64

**Platforms:** Local: virtualbox, vmware, qemu, hyperv | Enterprise: vsphere, proxmox | Other: none

**Spec count:** 4

---

### openwrt

**Spec name:** `openwrt`

**Include chain:** openwrt → ssh

**Installer type:** none

**Version ranges:** `24.10`

**Versions (1):** 24.10

**Architectures:** x86_64, aarch64

**Platforms:** Local: qemu, vmware | Enterprise: proxmox | Other: none

**Spec count:** 2

---

### OPNsense

**Spec name:** `opnsense`

**Include chain:** opnsense → ssh

**Installer type:** none

**Version ranges:** `25.7`

**Versions (1):** 25.7

**Architectures:** x86_64

**Platforms:** Local: qemu, vmware | Enterprise: proxmox | Other: none

**Spec count:** 1

---

### pfSense

**Spec name:** `pfsense`

**Include chain:** pfsense → ssh

**Installer type:** none

**Version ranges:** `2.7.2`

**Versions (1):** 2.7.2

**Architectures:** x86_64

**Platforms:** Local: qemu, vmware, virtualbox | Enterprise: proxmox | Other: none

**Spec count:** 1

---

### VMware Photon OS

**Spec name:** `photon`

**Include chain:** photon → linux → ssh

**Installer type:** photon-kickstart

**Version ranges:** `5.0`

**Versions (1):** 5.0

**Architectures:** x86_64, aarch64

**Platforms:** Local: virtualbox, vmware, qemu | Enterprise: vsphere, proxmox | Other: none

**Spec count:** 2

---

### Proxmox VE

**Spec name:** `proxmox-ve`

**Include chain:** proxmox-ve → linux → ssh

**Installer type:** answer.toml

**Version ranges:** `3.4, 4.4, 5.4, 6.4, 7.4, 8.4, 9.0, 9.1, 9.2`

**Versions (9):** 3.4, 4.4, 5.4, 6.4, 7.4, 8.4, 9.0, 9.1, 9.2

**Architectures:** x86_64

**Platforms:** Local: virtualbox, vmware, qemu | Enterprise: vsphere | Other: none

**Spec count:** 9

---

### SCO OpenServer

**Spec name:** `sco`

**Installer type:** none

**Version ranges:** `5.0.5`

**Versions (1):** 5.0.5

**Architectures:** i386

**Platforms:** Local: virtualbox, vmware

**Spec count:** 1

---

### solaris

**Spec name:** `solaris`

**Include chain:** solaris → ssh

**Installer type:** none

**Version ranges:** `11.4`

**Versions (1):** 11.4

**Architectures:** x86_64

**Platforms:** Local: qemu, vmware, virtualbox | Other: none

**Spec count:** 1

---

### TrueNAS

**Spec name:** `truenas`

**Include chain:** truenas → ssh

**Installer type:** none

**Version ranges:** `25.10`

**Versions (1):** 25.10

**Architectures:** x86_64

**Platforms:** Local: qemu, vmware | Enterprise: proxmox | Other: none

**Spec count:** 1

---

### UnixWare

**Spec name:** `unixware`

**Installer type:** none

**Version ranges:** `7.1`

**Versions (1):** 7.1

**Architectures:** i386

**Platforms:** Local: virtualbox, vmware

**Spec count:** 1

---

### VyOS

**Spec name:** `vyos`

**Include chain:** vyos → ssh

**Installer type:** none

**Version ranges:** `1.4`

**Versions (1):** 1.4

**Architectures:** x86_64

**Platforms:** Local: qemu, vmware | Enterprise: proxmox | Other: none

**Spec count:** 1

---

### windows-desktop

**Spec name:** `windows-desktop`

**Include chain:** windows-desktop → windows → winrm

**Installer type:** autounattend

**Version ranges:** `10, 11`

**Versions (2):** 10, 11

**Architectures:** x86_64

**Platforms:** Local: virtualbox, vmware, qemu, hyperv | Enterprise: vsphere, proxmox | Other: none

**Spec count:** 2

---

### XCP-ng

**Spec name:** `xcpng`

**Include chain:** xcpng → linux → ssh

**Installer type:** answerfile.xml

**Version ranges:** `8.2.1, 8.3`

**Versions (2):** 8.2.1, 8.3

**Architectures:** x86_64

**Platforms:** Local: virtualbox, vmware, qemu | Other: none

**Spec count:** 2

---
