# Configuration Merging

OSImager uses a hierarchical configuration merge system to assemble the final Packer build JSON from multiple layers of configuration files. Each layer can add, override, or selectively deep-merge values from previous layers. This document describes the complete merge pipeline and the mechanics of each stage.

## Merge Chain

Configuration is loaded in this fixed order. Later layers override earlier ones:

| Order | Source | Description | Example |
|-------|--------|-------------|---------|
| 1 | `all.json` | Base defaults shared by all platforms | `cpu_sockets:1`, `cpu_cores:2`, `memory:2048`, `boot_disk_size:16385` |
| 2 | Platform JSON | Builder type, boot commands, VM hardware, platform-specific defaults | `vsphere.json` sets `type: "vsphere-iso"`, network adapters, disk layout |
| 3 | Location JSON/TOML | Network settings, DNS, NTP, paths, per-platform overrides | `lab.toml` sets `domain`, `cidr`, `gateway`, `iso_path`, `vms_path` |
| 4 | Spec JSON | OS installer config, kickstart files, include chain | `alma/spec.json` sets ISO URLs, `cd_files`, `boot_command` |
| 5 | Specific sections | 6 types of conditional overrides applied recursively | `version_specific`, `platform_specific`, `arch_specific`, etc. |
| 6 | CLI `--define` | User overrides from the command line | `-D key=value,key2=value2` |

The chain is initiated by `make_build()` in `core.py` (line 964). It calls `load_data_file()` for each of the first four layers (platform at line 1026, location at line 1035, spec at line 1041), and layer 6 is applied at line 1169.

### Layer 1: all.json

The file `platforms/all.json` is loaded via the platform JSON's `"include": "all"` directive. It establishes the absolute baseline defaults:

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

Every platform JSON includes `all.json` through the include mechanism, so these values are always present unless explicitly overridden.

### Layer 2: Platform JSON

Platform files reside in `{data_dir}/platforms/{name}.json`. The platform file declares its `include` (typically `"all"`), then overlays platform-specific builder configuration. For example, `vsphere.json` defines the `config` section with `type: "vsphere-iso"`, network adapters, storage layout, and Packer builder fields.

### Layer 3: Location JSON/TOML

Location files reside in `{user_dir}/locations/` (i.e., `~/.config/osimager/locations/`). They can be JSON or TOML format. When both exist for the same name, JSON takes priority (see `load_data_file()` at line 453-461 in `core.py`).

Locations define the environment-specific settings: domain, CIDR, gateway, DNS servers, NTP servers, datastore paths, ISO paths, and VM output paths. They can also contain `platform_specific` sections that override platform-level settings for a particular site.

### Layer 4: Spec JSON

Spec files reside in `{data_dir}/specs/{name}/spec.json`. Specs define the OS distribution configuration: `provides` (dist, versions, arches), installer files, boot commands, provisioners, and the include chain to parent specs.

A typical include chain: `alma` -> `rhel` -> `linux` -> `ssh` -> (no further includes).

### Layer 5: Specific Sections

After each data file is loaded via `load_data()`, the method calls `load_specific()` which processes six types of conditional overrides in fixed order. These are described in detail below.

### Layer 6: CLI --define

User-supplied `--define key=value,key2=value2` pairs are parsed and injected directly into `self.defs` at line 1169-1178 of `core.py`. These override any previously set definition values.

---

## How load_data() Works

**Location:** `core.py`, lines 315-378.

`load_data()` is the central merge function. Every configuration file passes through it. It operates on 8 sections, each mapped to an instance attribute on the `OSImager` object:

| Section | Type | Instance Attribute |
|---------|------|--------------------|
| `files` | list | `self.files` |
| `evars` | dict | `self.evars` |
| `defs` | dict | `self.defs` |
| `variables` | dict | `self.variables` |
| `pre_provisioners` | list | `self.pre_provisioners` |
| `provisioners` | list | `self.provisioners` |
| `post_provisioners` | list | `self.post_provisioners` |
| `config` | dict | `self.config` |

### Merge Logic

For each section present in the incoming data:

1. **Dict sections** (`evars`, `defs`, `variables`, `config`): The existing dict is updated with `attr.update(new_val)`. This is a shallow merge -- keys in the new data overwrite keys in the existing data at the top level.

2. **List sections** (`files`, `pre_provisioners`, `provisioners`, `post_provisioners`): Behavior depends on the `method` key:
   - `method="merge"` (default): New items are appended via `attr.extend(new_val)`.
   - `method="replace"`: The existing list is cleared first (`attr[:] = []`), then the new items are added.

3. **Other types**: Assigned directly via `setattr()`.

The `method` key is popped from the data dict at line 331 before section processing begins. It defaults to `"merge"` if not present.

### Processing Order

```
load_data(data):
    method = data.pop('method', "merge")
    for section in [files, evars, defs, variables, pre_provisioners, provisioners, post_provisioners, config]:
        new_val = data.get(section)
        if new_val is None: continue
        attr = getattr(self, section)
        # process merge key (if dict)
        # apply dict update or list extend/replace
    load_specific(data)
```

After all 8 sections are processed, `load_data()` calls `load_specific(data)` to handle any conditional sections remaining in the data.

---

## The `merge` Key (Deep Merge)

**Location:** `core.py`, lines 342-354.

Within dict sections, a special `merge` key enables selective deep merging of nested structures instead of wholesale overwriting. This is critical for cases like VMware's `vmx_data` where multiple layers need to contribute key-value pairs to the same nested dict.

### Mechanics

When `new_val` is a dict, `load_data()` checks for a `merge` key:

```python
merge = new_val.pop("merge", [])
for key in merge:
    key_val = new_val.pop(key, None)
    if key_val:
        if key in attr:
            if isinstance(attr[key], dict):
                attr[key].update(key_val)
            elif isinstance(attr[key], list):
                attr[key].extend(key_val)
            else:
                attr[key] = key_val
        else:
            attr[key] = key_val
```

The `merge` key is a list of key names within the dict that should be deep-merged rather than replaced. These keys are popped from the incoming data and merged individually before the remaining keys undergo normal `attr.update(new_val)`.

### Example

In the RHEL spec's VMware `platform_specific`, the config section uses:

```json
{
  "config": {
    "merge": ["vmx_data"],
    "vmx_data": {
      "scsi0.virtualdev": "pvscsi"
    }
  }
}
```

Without the `merge` directive, the entire `vmx_data` dict from the platform level would be replaced. With it, the new key `scsi0.virtualdev` is added to the existing `vmx_data` dict while preserving keys set by previous layers.

### Behavior by Type

| Existing type | Incoming type | Merge behavior |
|---------------|---------------|----------------|
| dict | dict | `attr[key].update(key_val)` -- keys are merged |
| list | list | `attr[key].extend(key_val)` -- items are appended |
| other | any | `attr[key] = key_val` -- replaced outright |

---

## How load_specific() Works

**Location:** `core.py`, lines 294-313.

`load_specific()` processes conditional override sections that apply only when certain runtime values match. It operates on a fixed list of 6 specific types, processed in this exact order:

1. `platform_specific`
2. `location_specific`
3. `dist_specific`
4. `version_specific`
5. `arch_specific`
6. `firmware_specific`

### Matching Algorithm

For each specific type, `load_specific()`:

1. Constructs the data key by appending `_specific` to the type name (e.g., `version` -> `version_specific`).
2. Retrieves the current runtime value from `self.defs` using the type name as key (e.g., `self.defs["version"]`).
3. Iterates over each entry in the specific section's array.
4. Pops the type-name key from the entry (e.g., `entry.pop("version")`).
5. Tests the popped value against the runtime value using `re.fullmatch()` with `re.IGNORECASE`.
6. If matched, calls `load_data(entry)` with the remaining entry data.

```python
specifics = ["platform", "location", "dist", "version", "arch", "firmware"]
for section in specifics:
    name = self.defs.get(section, None)
    if name:
        specific_data = data.get(section + "_specific", [])
        for entry in specific_data:
            specific_data_name = entry.pop(section, "")
            if re.fullmatch(specific_data_name, name, re.IGNORECASE):
                self.load_data(entry, False)
```

### Recursive Application

Because `load_data()` calls `load_specific()` at the end, and `load_specific()` calls `load_data()` for each match, the system supports arbitrary nesting of specific sections. For example, a `version_specific` entry can contain a `platform_specific` section, which can contain an `arch_specific` section.

This recursion is visible in the RHEL spec: the `version_specific` entry for `7.*` contains a `platform_specific` array with entries for proxmox, virtualbox, vmware, and vsphere. When building `rhel-7.9-x86_64` on vsphere, the system matches version `7.*`, enters `load_data()` for that entry, which then triggers `load_specific()` again, matching platform `vsphere` and loading its overrides.

### Pattern Matching

The match values in specific sections are regex patterns passed to `re.fullmatch()`. Common patterns:

| Pattern | Matches |
|---------|---------|
| `8.*` | Any version starting with `8.` (e.g., `8.3`, `8.10`) |
| `[23].*` | Versions `2.x` or `3.x` |
| `proxmox` | Exact match for platform `proxmox` |
| `x86_64` | Exact match for architecture `x86_64` |

---

## How load_file() Handles Includes

**Location:** `core.py`, lines 421-442.

The include system enables spec inheritance. When a data file contains an `"include"` key, the referenced file(s) are loaded first, then the current file's data is applied on top.

### Include Processing

```python
def load_file(self, where, file_path):
    data = self.read_data(file_path)
    incs = data.pop("include", None)
    if incs:
        if isinstance(incs, list):
            for inc in incs:
                data = self.load_inc(where, inc, data)
        elif isinstance(incs, str):
            data = self.load_inc(where, incs, data)
    else:
        self.load_data(data)
    return data
```

The `include` key is popped from the data before processing. It can be:
- A **string**: A single spec name to include (e.g., `"include": "rhel"`).
- A **list**: Multiple spec names to include in order (e.g., `"include": ["ssh", "linux"]`).

### How load_inc() Works

**Location:** `core.py`, lines 404-419.

`load_inc()` orchestrates the include chain:

1. Calls `load_data_file()` to load the included file. This recursively processes that file's own includes.
2. Calls `load_data(data)` to apply the current file's sections to the imager state.
3. Calls `inc_data.update(data)` to merge the current file's raw data on top of the included file's raw data (for the returned dict).

The result: the included file's settings are loaded first, then the current file's settings overlay them. This means child specs override parent specs.

### Example Include Chain

For an AlmaLinux 9.3 build:

```
alma/spec.json
  -> includes "rhel"
     rhel/spec.json
       -> includes "linux"
          linux/spec.json
            -> includes "ssh"
               ssh/spec.json (base communicator config)
```

Each file in the chain is loaded bottom-up: `ssh` first, then `linux` overlays, then `rhel` overlays, then `alma` overlays.

---

## How load_data_file() Resolves Paths

**Location:** `core.py`, lines 444-469.

`load_data_file()` translates a logical name (e.g., `"vsphere"`) into a filesystem path based on the `where` parameter:

| `where` value | Path resolution |
|---------------|-----------------|
| `specs` | `{data_dir}/specs/{what}/spec.json` |
| `locations` | `{user_dir}/locations/{what}.json` or `{what}.toml` (JSON takes priority) |
| `platforms` | `{data_dir}/platforms/{what}.json` |

### Location Resolution Detail

For locations, the method checks for both JSON and TOML files:

```python
if where == 'locations':
    loc_dir = os.path.join(self.settings['user_dir'], "locations")
    if not what.endswith(('.json', '.toml')):
        json_path = os.path.join(loc_dir, what + ".json")
        toml_path = os.path.join(loc_dir, what + ".toml")
        file_path = json_path if os.path.exists(json_path) else toml_path
```

If the name already has an extension, it is used as-is. Otherwise, JSON is checked first.

### Extension Handling

For non-location files, `.json` is appended if not already present (line 465-466).

After resolving the path, `load_data_file()` delegates to `load_file()` which handles reading, include processing, and data loading.

---

## Complete Build Assembly

The full merge sequence executed by `make_build()` (line 964) produces the final Packer build configuration:

1. **Initialize** default environment variables and provisioners (lines 999-1021).
2. **Load platform**: `load_data_file("platforms", platform_name)` (line 1026).
3. **Load location**: `load_data_file("locations", location_name)` (line 1035).
4. **Load spec**: `load_file("specs", spec_path)` (line 1041).
5. **Set computed defs**: version parts, paths, network config, DNS, NTP (lines 1094-1178).
6. **Apply CLI defines**: user `--define` overrides (lines 1169-1178).
7. **Run template substitution**: `do_sub()` on all sections (lines 1223-1237).
8. **Assemble build JSON**: variables, provisioners (pre + main + post), builders (lines 1248-1252).
9. **Resolve Packer vault refs**: when using config-based secrets (line 1255-1256).

The resulting `self.build` dict is the final Packer JSON written to the temp directory and passed to `packer build`.
