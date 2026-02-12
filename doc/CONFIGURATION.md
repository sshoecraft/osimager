# OSImager Configuration File Format

## 🎯 Overview

OSImager uses a flexible JSON-based configuration system that supports conditional logic, variable substitution, and hierarchical inheritance. This document describes the complete structure and capabilities of OSImager configuration files.

## 📁 Configuration File Types

### 1. Platform Files (`/data/platforms/*.json`)
Define virtualization platform settings for Packer builders (VMware, VirtualBox, QEMU, etc.)

### 2. OS Specification Files (`/data/specs/*/spec.json`)
Define operating system build specifications with provisioning logic

### 3. Location Files (`/data/locations/*.json`)
Define environment-specific configurations (dev, lab, production)

## 🧱 Core Structure

### Standard Sections

All configuration files can contain these sections:

| Section | Purpose | Example Use Case |
|---------|---------|------------------|
| `files` | File generation and templates | Creating kickstart files, cloud-init configs |
| `evars` | Environment variables | Setting PATH, build environment |
| `defs` | Variable definitions | CPU count, memory size, disk size |
| `variables` | Additional variables | Complex calculations, derived values |
| `pre_provisioners` | Pre-build actions | Download ISOs, prepare environments |
| `provisioners` | Main provisioning | Ansible playbooks, shell scripts |
| `post_provisioners` | Post-build actions | Cleanup, notifications, uploads |
| `config` | Platform configuration | Packer builder settings |

### Section Modifiers

Each section supports conditional modifiers for different environments:

| Modifier | Purpose | Values |
|----------|---------|--------|
| `platform_specific` | Platform-dependent settings | vmware, virtualbox, qemu, libvirt, proxmox, vsphere, hyperv |
| `location_specific` | Environment-dependent settings | dev, lab, production, local, pnet |
| `dist_specific` | Distribution-specific settings | rhel, centos, almalinux, rocky, debian, ubuntu |
| `version_specific` | Version-dependent settings | 9.0, 9.1, 9.2, etc. (supports regex) |
| `arch_specific` | Architecture-dependent settings | x86_64, aarch64, i386, ppc64le |

## 🔗 Modifier Nesting Rules

### 1. Modifiers Can Contain Sections
```json
{
  "platform_specific": [
    {
      "platform": "vmware",
      "defs": {
        "cpu_sockets": 2
      },
      "config": {
        "guest_os_type": "rhel9-64"
      }
    }
  ]
}
```

### 2. Sections Can Contain Modifiers
```json
{
  "defs": {
    "base_memory": 2048,
    "arch_specific": [
      {
        "arch": "aarch64",
        "defs": {
          "memory": 4096
        }
      }
    ]
  }
}
```

### 3. Modifiers Can Contain Other Modifiers
```json
{
  "platform_specific": [
    {
      "platform": "vmware",
      "version_specific": [
        {
          "version": "9.0",
          "arch_specific": [
            {
              "arch": "x86_64",
              "config": {
                "guest_os_type": "rhel9-64"
              }
            }
          ]
        }
      ]
    }
  ]
}
```

## 📄 Spec File Additional Fields

OS specification files require additional top-level fields:

### Mandatory Fields

#### `provides` (required)
Defines what the spec provides:
```json
{
  "provides": {
    "dist": "rhel",
    "versions": ["9.[0-10]", "9.latest"],
    "arches": ["x86_64", "aarch64", "ppc64le"]
  }
}
```

- **`dist`** (string): Distribution identifier
- **`versions`** (array): Supported versions (regex wildcards supported)
- **`arches`** (array): Supported architectures

### Optional Fields

#### `include` (string)
Include another spec as a base:
```json
{
  "include": "rhel-base"
}
```

#### `flavor` (string)
Operating system family:
```json
{
  "flavor": "Linux"  // or "Windows"
}
```

#### `platforms` (array)
Supported platforms (omit for all platforms):
```json
{
  "platforms": ["vmware", "virtualbox", "qemu"]
}
```

#### `communicator` (string)
Connection method for provisioning:
```json
{
  "communicator": "ssh"  // or "winrm"
}
```

#### `venv` (string)
Python virtual environment for Packer execution:
```json
{
  "venv": "osimager-env"
}
```

#### `files` (array)
File generation definitions:
```json
{
  "files": [
    {
      "sources": [
        ">>spec_dir<</kickstart.cfg",
        "files/linux/ks-part.sh"
      ],
      "dest": ">>tmpdir<</kickstart.cfg"
    }
  ]
}
```

## 🔧 Variable Substitution

OSImager supports several variable substitution syntaxes:

### Basic Variable Substitution
```json
{
  "vm_name": ">>name<<",
  "output_directory": ">>vms_path<</>>name<<"
}
```

### Numeric Expression Evaluation
```json
{
  "cpus": "#>cpu_sockets*cpu_cores<#",
  "memory": "#>base_memory*memory_multiplier<#"
}
```

### Content Inclusion
```json
{
  "cd_files": "%>cd_files<%",
  "boot_files": "%>boot_file_list<%"
}
```

### Python Expression Evaluation
```json
{
  "iso_url": "E>'>>iso_path<<>>iso_name<<' if >>local_only<< else '>>iso_url<<'<E",
  "iso_checksum": "E>'>>iso_checksum<<' if len('>>iso_checksum<<') else 'none'<E"
}
```

## 📋 Complete Example

Here's a comprehensive example showing all concepts:

```json
{
  "provides": {
    "dist": "rhel",
    "versions": ["9.[0-10]"],
    "arches": ["x86_64", "aarch64"]
  },
  "flavor": "Linux",
  "include": "rhel-base",
  "files": [
    {
      "sources": [
        ">>spec_dir<</kickstart.cfg",
        "files/linux/kickstart_post.cfg"
      ],
      "dest": ">>tmpdir<</kickstart.cfg"
    }
  ],
  "defs": {
    "cpu_cores": 4,
    "base_memory": 4096,
    "arch_specific": [
      {
        "arch": "aarch64",
        "defs": {
          "base_memory": 8192
        }
      }
    ]
  },
  "config": {
    "firmware": "efi",
    "boot_wait": "10s",
    "memory": "#>base_memory<#",
    "cpus": "#>cpu_cores<#"
  },
  "platform_specific": [
    {
      "platform": "vmware",
      "defs": {
        "cpu_sockets": 2
      },
      "config": {
        "guest_os_type": "rhel9-64",
        "vmx_data": {
          "scsi0.virtualdev": "pvscsi"
        }
      },
      "version_specific": [
        {
          "version": "9.0",
          "defs": {
            "iso_url": "https://archive.org/download/rhel-9.0/rhel-baseos-9.0->>arch<<-dvd.iso"
          }
        }
      ]
    },
    {
      "platform": "virtualbox",
      "config": {
        "guest_os_type": "RedHat9_64"
      }
    }
  ],
  "version_specific": [
    {
      "version": "9.0",
      "defs": {
        "iso_checksum": "sha256:1234567890abcdef..."
      }
    }
  ],
  "provisioners": [
    {
      "type": "ansible",
      "playbook_file": ">>tasks_dir<</rhel-hardening.yml"
    }
  ]
}
```

## 🎯 Evaluation Order

OSImager processes configurations in this order:

1. **Base configuration** loaded
2. **Include files** merged (if specified)
3. **Platform-specific** sections applied
4. **Location-specific** sections applied
5. **Distribution-specific** sections applied
6. **Version-specific** sections applied
7. **Architecture-specific** sections applied
8. **Variable substitution** performed
9. **Final configuration** generated

## ✅ Validation Rules

### Required Fields
- Spec files must have `provides.dist`, `provides.versions`, `provides.arches`
- Platform files must have valid Packer configuration
- All files must be valid JSON

### Naming Conventions
- File names: lowercase with hyphens (`rhel-9`, `vmware-iso`)
- Variables: snake_case (`cpu_cores`, `base_memory`)
- Platforms: lowercase (`vmware`, `virtualbox`, `qemu`)

### Version Matching
- Exact match: `"9.0"`
- Range match: `"9.[0-5]"`
- Wildcard: `"9.latest"`
- Multiple: `["9.0", "9.1", "9.2"]`

## 🔍 Best Practices

### 1. Use Inheritance
```json
{
  "include": "linux-base",
  "platform_specific": [
    {
      "platform": "vmware",
      "include": "vmware-defaults"
    }
  ]
}
```

### 2. Minimize Duplication
Use modifiers to avoid repeating similar configurations:
```json
{
  "defs": {
    "base_disk_size": 40000
  },
  "version_specific": [
    {
      "version": "9.[0-2]",
      "defs": {
        "disk_size": "#>base_disk_size<#"
      }
    },
    {
      "version": "9.[3-10]",
      "defs": {
        "disk_size": "#>base_disk_size+10000<#"
      }
    }
  ]
}
```

### 3. Document Complex Logic
```json
{
  "config": {
    // Reason: RHEL 9.0-9.2 requires legacy BIOS for compatibility
    "firmware": "E>'bios' if '>>version<<'.startswith('9.0') or '>>version<<'.startswith('9.1') or '>>version<<'.startswith('9.2') else 'efi'<E"
  }
}
```

### 4. Validate Platform Support
```json
{
  "platforms": ["vmware", "virtualbox"],
  "platform_specific": [
    {
      "platform": "proxmox",
      "config": {
        "note": "Experimental support - use with caution"
      }
    }
  ]
}
```

This configuration system provides the flexibility needed for complex multi-platform, multi-version, multi-architecture build scenarios while maintaining readability and avoiding configuration duplication.
