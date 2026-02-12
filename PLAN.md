# OSImager Development Plan

## System Architecture

### Overview

OSImager builds VM images using HashiCorp Packer. It provides a hierarchical JSON configuration system that generates Packer templates dynamically, with Ansible for provisioning. The system has three interfaces: CLI tools, a FastAPI REST API with WebSocket support, and a React/TypeScript frontend.

### Core Engine (`lib/osimager/core.py`, 1239 LOC)

The `OSImager` class orchestrates the entire build pipeline:

1. **Configuration Resolution**: Merges platform + location + spec configs hierarchically
2. **Template Substitution**: 12 action types for dynamic value injection (see Template System below)
3. **Packer Generation**: Creates Packer JSON from resolved configuration
4. **File Assembly**: Concatenates template fragments into kickstart/preseed files
5. **Build Execution**: Runs Packer with generated config, monitors output

Key methods:
- `init_settings()` - Argument parsing, settings loading
- `load_data_file()` - JSON loading with include resolution
- `load_specific()` - Applies version/arch/platform/firmware-specific overrides
- `make_build()` - Core build configuration assembly
- `gen_files()` - Template file concatenation
- `run_packer()` - Packer execution

### Template Substitution System (`lib/osimager/utils.py`, 681 LOC)

| Syntax | Type | Example |
|--------|------|---------|
| `>>variable<<` | Variable substitution | `>>arch<<`, `>>version<<`, `>>temp_dir<<` |
| `%>variable<%` | Alternative syntax | `%>cd_files<%` |
| `+>variable<+` | Basename | `+>iso_url<+` |
| `*>variable<*` | DNS/IP lookup | `*>hostname<*` |
| `\|>path<\|` | Vault secret | `\|>images/linux:password<\|` |
| `#>expr<#` | Math expression | `#>cpu_sockets*cpu_cores<#` |
| `$>VAR<$` | Environment variable | `$>HOME<$` |
| `1>path<1` | MD5 hash | `1>images/linux:password<1` |
| `5>path<5` | SHA256 hash | `5>images/linux:password<5` |
| `6>path<6` | SHA512 hash | `6>images/linux:password<6` |
| `E>expr<E` | Conditional eval | `E>'efi' if >>major<< >= 7 else 'bios'<E` |
| `[>list<]` | List expansion | `[>ansible_extra_args<]` |

### Engine Variables (set in `make_build()`, lines 970-981)

| Variable | Source | Description |
|----------|--------|-------------|
| `>>temp_dir<<` | Auto-generated | Temp build directory (absolute path) |
| `>>tmpdir<<` | Same as temp_dir | Alias for temp_dir |
| `>>spec_dir<<` | `os.path.dirname(spec_path)` | Absolute path to spec's directory |
| `>>dist<<` | From target path | Distribution name (rhel, alma, etc.) |
| `>>version<<` | From target path | Version string (6.9, 9.0, etc.) |
| `>>major<<` | Derived from version | Major version number |
| `>>minor<<` | Derived from version | Minor version number |
| `>>arch<<` | From target path | Architecture (x86_64, aarch64, etc.) |
| `>>base_path<<` | Settings | Base installation path |
| `>>data_path<<` | Settings | Data directory path |

Note: `>>spec_path<<` is NOT defined in defs. Old specs using it need `>>spec_dir<<`.

### File Resolution

**`gen_files()` (line 1127-1161):**
- `files.sources` paths resolve relative to `data/files/` (line 1135: `files_path = os.path.join(data_dir, "files")`)
- `files.dest` is just the filename; auto-joined with `temp_dir` (line 1157)
- Before gen_files runs, the engine `os.chdir(data_path)` (line 1168-1171)

**`ansible_playbook`:**
- Default value: `"config.yml"` (from settings, line 52)
- Set in defs at line 897: `self.defs['ansible_playbook'] = self.settings['ansible_playbook']`
- Packer runs from `data/` directory, so `config.yml` resolves to `data/config.yml` (the main Ansible playbook)
- Spec-specific config goes in `spec_config` defs variable, passed to Ansible as `spec-config` extra var

---

## Configuration Hierarchy

### Directory Structure

```
data/
├── platforms/          # Virtualization platform configs
│   ├── vmware.json     # VMware Workstation/Fusion
│   ├── vsphere.json    # vSphere/ESXi remote
│   ├── virtualbox.json # Oracle VirtualBox
│   ├── qemu.json       # QEMU/KVM
│   ├── libvirt.json    # Libvirt
│   ├── proxmox.json    # Proxmox VE
│   └── all.json        # Aggregate metadata
├── locations/          # Environment configs
│   ├── dev.json        # Development
│   ├── lab.json        # Lab/testing
│   ├── local.json      # Local/offline
│   └── pnet.json       # Production network
├── specs/              # OS specifications (ONE file per distro family)
│   ├── ssh/spec.json   # SSH communicator base
│   ├── linux/spec.json # Linux base (includes ssh)
│   ├── redhat/spec.json # All RHEL versions (includes linux)
│   ├── esxi/spec.json  # All ESXi versions
│   └── alma.json       # AlmaLinux (includes redhat)
├── files/              # Template fragments for file assembly
│   ├── redhat/         # RHEL kickstart fragments
│   ├── linux/          # Shared Linux files (banner, findcd)
│   └── esxi/           # ESXi VIB files
├── tasks/              # Ansible playbooks for provisioning
├── config.yml          # Main Ansible playbook entry point
└── ansible.cfg         # Ansible configuration
```

### Include/Inheritance Chain

```
ssh/spec.json          → SSH communicator config
  └── linux/spec.json  → boot_disk_size, vault SSH credentials
      └── redhat/spec.json → All RHEL versions, kickstart assembly, platform configs
          └── alma.json    → AlmaLinux (overrides dist, versions, ISO)
          └── centos.json  → CentOS (future, overrides dist, versions, ISO)
          └── rocky.json   → Rocky Linux (future, overrides dist, versions, ISO)
          └── oel.json     → Oracle Linux (future, overrides dist, versions, ISO)

esxi/spec.json         → All ESXi versions (standalone, no include chain yet)
winrm/spec.json        → WinRM communicator config (needs creation)
  └── windows.json     → Windows (future, includes winrm)
```

### Spec Resolution Order

When building `vmware/lab/rhel-6.9-x86_64`:
1. Load platform: `data/platforms/vmware.json`
2. Load location: `data/locations/lab.json`
3. Load spec via index: `data/specs/redhat/spec.json`
4. Process includes: linux → ssh (bottom-up merge)
5. Apply version_specific matching `6.*` and `6.9`
6. Apply arch_specific matching `x86_64`
7. Apply platform_specific matching `vmware`
8. Apply firmware_specific if applicable
9. Substitute all template variables
10. Generate files (kickstart assembly)
11. Run Packer

---

## Spec Format Reference

### Single-File-Per-Distro Pattern

Each distribution family gets ONE spec file containing ALL versions. Version differences are handled via `version_specific`. The ESXi spec is the reference example — it covers ESXi 5.5 through 8.0 in a single file with version/platform/firmware specificity.

### Top-Level Fields

```json
{
  "provides": {
    "dist": "rhel",
    "versions": ["6.[9,10]", "7.[5-9]", "8.[0-10]", "9.[0-10]"],
    "arches": ["i386", "x86_64", "aarch64"]
  },
  "include": "linux",
  "method": "merge",
  "platforms": ["virtualbox", "vmware", "vsphere", "proxmox"],
  "venv": "2.10",
  "files": [...],
  "defs": {...},
  "variables": {...},
  "evars": {...},
  "config": {...},
  "pre_provisioners": [...],
  "post_provisioners": [...],
  "version_specific": [...],
  "platform_specific": [...],
  "firmware_specific": [...]
}
```

### Specificity Hierarchy (nesting supported)

```
spec (base)
├── version_specific[]
│   ├── defs, config, files, variables, evars
│   └── arch_specific[]
│       └── defs, config
├── platform_specific[]
│   ├── defs, config
│   ├── version_specific[] (nested!)
│   │   └── defs, config, files
│   └── firmware_specific[] (nested!)
│       └── config
└── firmware_specific[]
    └── config
```

### Merge vs Replace

- `"method": "merge"` (default) — deep merge: objects combine, arrays append
- `"method": "replace"` — completely replaces parent values
- `"merge": ["field1", "field2"]` — selectively merge specific fields (e.g., vmx_data)

---

## Current State

### What Works
- Core engine (`lib/osimager/core.py`) — complete, handles full build pipeline
- Template substitution (`lib/osimager/utils.py`) — all 12 action types implemented
- CLI tools (`bin/mkosimage`, `bin/rfosimage`, `bin/mkvenv`) — functional
- Frontend (`frontend/`) — complete 8-page React/TypeScript SPA, built in `frontend/dist/`
- Backend (`backend/`) — FastAPI with WebSocket, but has startup issue (shuts down immediately)
- Configuration system — hierarchical JSON with platform/location/spec merge
- ESXi spec — complete reference implementation covering 5 versions

### What Needs Fixing

**RHEL 6 spec (`data/specs/redhat/spec.json`):**
- `spec_config` references `"specs/redhat/config_6.yml"` which does not exist. Should be `">>spec_dir<</config.yml"` or similar, pointing to a config.yml in the spec directory
- `variables` section has hardcoded credentials (vsphere password, SSH password) — should use vault
- `install_notice` has placeholder `"blah"`
- Only defines RHEL 6.9 and 6.10 — needs expansion for other versions

**Backend (`backend/`):**
- Shuts down immediately on startup (visible in `backend/osimager-api.log`)
- Log file references old `api/` directory path (was renamed to `backend/`)
- CORS allows all origins (`["*"]`)

**File organization:**
- ESXi kickstart files are in `data/specs/esxi/` but gen_files() resolves from `data/files/`
- Need to verify RHEL kickstart fragments in `data/files/redhat/` are complete and correct

**Version inconsistency:**
- `core.py` VERSION = "1.0"
- `constants.py` OSIMAGER_VERSION = "0.1.0"
- `scripts/__init__.py` __version__ = "0.1.0"

**Stale files:**
- `core.py.backup`, `core.py.save`, `core.py.save2` in `lib/osimager/`
- `spec.json.save`, `spec.json.save2` in `data/specs/esxi/`
- Empty `data/specs/xx/` directory

### Environment

- Machine: Apple Silicon (arm64/aarch64)
- Packer: 1.13.1 (outdated, 1.15.0 available)
- VirtualBox: 7.1.10
- VMware Fusion: installed
- ISOs at `/iso/`: ~100+ ISOs, ALL x86_64/amd64/i386 — no ARM64 ISOs
- No git repository initialized

---

## Immediate Plan: Get RHEL 6 Running

### Step 1: Fix redhat/spec.json

- Fix `spec_config` path reference
- Verify `files.sources` all resolve correctly under `data/files/redhat/`
- Verify kickstart fragments exist: `rhel_6_kickstart.cfg`, `ks-part.sh`, `kickstart_end.cfg`, `kickstart_post.cfg`, `install_vmwtools.sh`
- Ensure `data/specs/redhat/` has a proper `config.yml` for Ansible provisioning

### Step 2: Verify CLI Pipeline

```bash
# List available specs — should show rhel-6.9-x86_64, rhel-6.10-x86_64
python3 bin/mkosimage.py --list

# Dry run to see generated Packer config
python3 bin/mkosimage.py --dry vmware/local/rhel-6.9-x86_64

# Debug mode for verbose output
python3 bin/mkosimage.py --debug --dry vmware/local/rhel-6.9-x86_64
```

### Step 3: Fix Issues Found in Dry Run

Likely issues:
- Missing files referenced in `files.sources`
- Template variables not resolving
- Platform config mismatches
- Packer command generation errors

### Step 4: Attempt Build (if ISOs available)

RHEL 6.9/6.10 x86_64 ISOs exist at `/iso/`:
- `rhel-server-6.9-x86_64-dvd.iso` (42MB — likely incomplete/corrupt)
- `rhel-server-6.10-x86_64-dvd.iso` (3.8GB — looks valid)

Note: These are x86_64 ISOs on an ARM64 machine. VMware Fusion can emulate x86_64 (slowly). VirtualBox ARM64 cannot run x86_64 guests.

---

## Migration Plan: Adding Versions to redhat/spec.json

Once RHEL 6 works, expand `data/specs/redhat/spec.json` to cover all RHEL versions. The `>>major<<` template in `files.sources` (`"redhat/kickstart_>>major<<.cfg"`) already supports this — add kickstart files per major version to `data/files/redhat/`.

### Version Expansion

Add to `provides.versions`:
```json
"versions": [
    "5.[1,9,10,11]",
    "6.[9,10]",
    "7.[5,6,7,8,9]",
    "8.[0-10]",
    "9.[0-10]"
]
```

Add to `provides.arches`:
```json
"arches": ["i386", "x86_64", "aarch64"]
```

### version_specific Entries Needed

Each major version needs overrides for:
- Boot command differences (BIOS vs EFI, different key sequences)
- Firmware (BIOS for 5/6, EFI for 7+)
- ISO URLs per version+arch
- SSH compatibility (older key exchange for 5/6)
- Ansible Python interpreter (python2 for 5/6, python3 for 7+)
- Guest OS types per platform per version

Source data for these entries comes from:
- `~/src/oldosimager/specs/rhel-{5,7,8,9}/spec.json`
- `~/src/x/osimager/specs/rhel-{5,6,7,8,9}/spec.json`

### Kickstart Files to Add

For each major version, add to `data/files/redhat/`:
- `kickstart_5.cfg` (from old rhel-5)
- `kickstart_6.cfg` (already exists as `rhel_6_kickstart.cfg`)
- `kickstart_7.cfg` (from old rhel-7)
- `kickstart_8.cfg` (from old rhel-8)
- `kickstart_9.cfg` (from old rhel-9)

### Config Files

Per-version Ansible configs go in `data/specs/redhat/` or are referenced via `spec_config`:
- `config_5.yml` (RHEL 5 specific — python2, older package management)
- `config_6.yml` (RHEL 6 specific)
- `config_7.yml` (RHEL 7+)

---

## Migration Plan: Other Distros

After RHEL is complete, create consolidated specs for other distro families:

### Derivative Distros (include redhat)

These are simple — just override `provides` and ISO URLs:

| Spec File | Dist | Includes | Versions |
|-----------|------|----------|----------|
| `centos.json` | centos | redhat | 5.x, 6.x, 7.x |
| `alma.json` | alma | redhat | 8.9, 9.2 |
| `rocky.json` | rocky | redhat | 9.5 |
| `oel.json` | oel | redhat | 5.x, 6.x |

### Standalone Distros

| Spec File | Dist | Versions | Notes |
|-----------|------|----------|-------|
| `debian/spec.json` | debian | 8-12 | Needs preseed files, different boot process |
| `sysv/spec.json` | sysvr4 | - | VirtualBox only, UNIX |
| `windows.json` | windows | - | Needs winrm/spec.json base first |

### WinRM Base

Create `data/specs/winrm/spec.json` from `~/src/oldosimager/old2/communicators/winrm.json`:
```json
{
  "config": {
    "communicator": "winrm",
    "winrm_host": "E>'>>fqdn<<' if '>>ip<<' == 'dhcp' else '>>ip<<'<E",
    "winrm_use_ssl": false,
    "winrm_username": "{{ user `winrm-username` }}",
    "winrm_password": "{{ user `winrm-password` }}",
    "winrm_timeout": "4h"
  }
}
```

---

## Source Material Locations

| Location | Description |
|----------|-------------|
| `~/src/osimager/` | Current project (this repo) |
| `~/src/oldosimager/specs/` | Old per-version specs (18 specs) |
| `~/src/x/osimager/specs/` | Intermediate version with per-version specs |
| `~/src/oldosimager/old2/communicators/` | WinRM communicator configs |
| `~/src/oldosimager/old2/flavors/` | Old flavor configs (windows) |
| `/iso/` | ISO library (~350GB, all x86_64/i386) |

---

## Backend/Frontend Status

### Backend (`backend/`)
- FastAPI with 6 routers: specs, builds, status, platforms, locations, config
- WebSocket for real-time build monitoring
- BuildManager with priority queue, concurrent builds
- Integration via CLI subprocess (shells out to mkosimage)
- Immediate shutdown bug — needs investigation
- All state in-memory (lost on restart)

### Frontend (`frontend/`)
- React 18 + TypeScript + Vite
- Tailwind CSS + Headless UI
- Zustand state management, TanStack React Query
- WebSocket client with reconnection
- 8 complete pages: Dashboard, Builds, New Build, Build Details, Specs, Platforms, Locations, Settings
- Built output in `frontend/dist/`

### Web Ports
- Frontend: http://localhost:3000 (dev)
- Backend: http://localhost:8000
- API docs: http://localhost:8000/docs

---

## Known Security Issues

1. **eval() in utils.py** — `E>` and `#>` template types use Python eval()
2. **CORS wide open** — `allow_origins=["*"]` in backend
3. **Hardcoded credentials** — vsphere/SSH passwords in redhat/spec.json
4. **os.system()** — Some shell command execution without proper escaping
5. **Weak password hashing** — MD5/SHA for kickstart passwords (may be intentional for kickstart compatibility)
