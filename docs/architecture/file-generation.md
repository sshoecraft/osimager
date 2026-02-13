# File Generation

OSImager generates installer configuration files (kickstart, preseed, cloud-init, AutoYaST, Autounattend) at build time by assembling template fragments and applying template substitution.

## How It Works

### The `files` Array

Each spec can define a `files` array. Each entry specifies source fragments to concatenate and a destination filename:

```json
{
  "files": [
    {
      "sources": [
        "rhel/kickstart_8.cfg",
        "rhel/ks-part.sh",
        "rhel/kickstart_end.cfg",
        "rhel/kickstart_post.cfg"
      ],
      "dest": "ks.cfg"
    }
  ]
}
```

Source paths are relative to `osimager/data/files/`.

### The `gen_files()` Method

`gen_files()` (core.py:1300-1334) processes the files array:

1. Apply `do_sub()` to the files array itself (resolves `>>major<<` in source paths like `rhel/kickstart_>>major<<.cfg`).
2. For each entry in the array:
   - Read each source file from `osimager/data/files/`.
   - Concatenate all sources in order into a single string.
   - Apply `do_substr()` on the concatenated content — all 12 substitution actions run against the full text.
   - Write the result to `{temp_dir}/{dest}`.

Source filenames can contain template markers. For example, RHEL uses `rhel/kickstart_>>major<<.cfg` which resolves to `rhel/kickstart_8.cfg` or `rhel/kickstart_9.cfg` based on the version being built.

### When gen_files() Runs

`gen_files()` is called from `run_packer()` (core.py:1350), after changing to the data directory and checking required files, but before writing the Packer JSON and executing packer.

## Installer Types by Distribution

### Kickstart (RHEL Family, ESXi)

**Used by:** RHEL, CentOS, AlmaLinux, Rocky Linux, Oracle Linux, ESXi

Kickstart files are assembled from versioned fragments in `data/files/rhel/`:

- `kickstart_3.cfg` through `kickstart_10.cfg` — version-specific base configs
- `ks-part.sh` — partition script
- `kickstart_end.cfg` — final section
- `kickstart_post.cfg` — post-install script
- `install_vmwtools.sh` — VMware tools installation (for VMware/vSphere platforms)

The `version_specific` entries in the RHEL spec select which kickstart fragment to use based on the major version. For example, RHEL 8.x uses `kickstart_8.cfg`.

Template variables in kickstart files include:

- `>>name<<` — hostname
- `>>domain<<` — DNS domain
- `>>ip<<`, `>>gateway<<`, `>>netmask<<` — network config
- `>>dns1<<`, `>>dns2<<` — DNS servers
- `>>ntp1<<` — NTP server
- `6>images/linux:password<6` — SHA512 root password hash
- `|>images/linux:username<|` — root username

ESXi uses its own kickstart files in `data/files/esxi/`.

Oracle Linux overrides the RHEL kickstart for version 6 with a custom `kickstart_6.cfg` in `data/files/oel/`.

### Preseed (Debian, Ubuntu 18.04)

**Used by:** Debian 8-9, Ubuntu 18.04

Preseed files are debconf answer files in `data/files/debian/`:

- `debian.seed` — main preseed template
- `debian.fix` — post-install fix script

Template variables include network configuration, DNS, timezone, and password hashes.

### Cloud-Init (Debian 10+, Ubuntu 20.04+)

**Used by:** Debian 10+, Ubuntu 20.04+

Cloud-init configuration in `data/files/ubuntu/` (also used by modern Debian):

- `user-data` — cloud-init user-data YAML
- `meta-data` — cloud-init meta-data

These are served via a virtual CD with label `cidata` (set via `cd_label` def). The boot command references the `autoinstall` endpoint.

### AutoYaST (SLES)

**Used by:** SLES 12.x, 15.x, 16.x

AutoYaST XML configuration files in `data/files/sles/`:

- `autoinst_12.xml` — SLES 12 configuration
- `autoinst_15.xml` — SLES 15 configuration
- `autoinst_16.xml` — SLES 16 configuration

The `version_specific` entries select the appropriate XML file based on the major version.

### Autounattend (Windows)

**Used by:** Windows, Windows Server

XML answer file in `data/files/windows/`:

- `Autounattend.xml` — unattended Windows installation configuration

Contains product keys, disk partitioning, locale settings, and administrator credentials via template substitution.

## How Files Flow Into the Build

1. Generated files are written to `temp_dir` (a temporary directory created per build).
2. The platform config references these files via `cd_files` or `cd_content` in the Packer builder:
   ```json
   "cd_files": "%>cd_files<%"
   ```
   The `cd_files` def is typically set to `>>temp_dir<</ks.cfg` (for kickstart) or a list of files.
3. The `cd_label` def controls the CD volume label:
   - `OEMDRV` — for RHEL kickstart (auto-detected by anaconda)
   - `cidata` — for cloud-init (standard cloud-init label)
   - `media` — for some other distributions
4. The boot command tells the installer where to find the config file:
   - Kickstart: `ks=cdrom:/ks.cfg`
   - Preseed: `auto url=cdrom:/preseed.cfg`
   - Cloud-init: `autoinstall ds=nocloud;`

## Common Files

`data/files/linux/` contains files used across distributions:

- `banner` — MOTD banner template
- `findcd` — helper script for finding the CD-ROM device

## Ansible Provisioning

After the OS is installed, Packer runs Ansible for post-install configuration.

### Default Provisioner

The default Ansible provisioner is created in `make_build()` (core.py:1010-1019):

```json
{
  "type": "ansible",
  "playbook_file": ">>ansible_playbook<<",
  "extra_arguments": [
    "[>ansible_extra_args<]",
    "--extra-vars",
    "platform={{user `platform-name`}} location_name={{user `location-name`}} spec_name={{user `spec-name`}} ..."
  ]
}
```

The playbook defaults to `config.yml` (configurable via `ansible_playbook` setting).

### Task Files

`data/tasks/` contains 23 Ansible task files imported by `data/ansible/config.yml`:

- `Debian_pre.yml`, `Linux_post.yml` — per-OS-family pre/post tasks
- `spec.yml` — spec-specific tasks
- `copy_files_if.yml` — conditional file copying
- `vsphere_post.yml` — vSphere-specific post-processing
- `rhel_6_config.yml` — RHEL 6 specific configuration
- And more per-distro and per-platform task files

The main playbook uses Ansible conditionals to select which tasks to run based on the platform, distribution, and version passed via extra vars.

### Pre and Post Provisioners

Specs can define `pre_provisioners` (run before the main Ansible provisioner) and `post_provisioners` (run after). These are used for platform-specific setup like VMware tools installation or cloud-specific cleanup.

## Required Files

Specs can declare files that must be downloaded separately before building:

```json
{
  "required_files": [
    {
      "file": "esxi/VMware-ESXi-8.0-Update2-patches.zip",
      "description": "ESXi 8.0 Update 2 VIB patch",
      "url": "https://vmware.com/path/to/download",
      "location": "esxi"
    }
  ]
}
```

`check_required_files()` (core.py:1267-1298) validates these before `gen_files()` runs. If any are missing, it prints the file description, download URL, and expected location, then exits.

Currently used by ESXi specs for VMware Tools VIB files that can't be redistributed.
