# OSImager Documentation Implementation Plan

## Prerequisites (do before docs)

### Add Missing Platforms
Port from archive (regressions — these worked in production):
- azure (azure-arm, boot: false, marketplace images)
- gcp (googlecompute, boot: false, source image families)
- xenserver (xenserver-iso, boot: true, ISO-based)
- none (null builder, provisioning-only)

Add new:
- aws (amazon-ebs, boot: false, AMI-based)
- hyperv (hyperv-iso, boot: true, ISO-based)

Fill in:
- libvirt (currently empty file)

Cloud platforms require per-distro `platform_specific` entries in spec files
for image references (azure: publisher/offer/sku, gcp: source_image_family,
aws: source_ami_filter). Archive files have the azure and gcp data already.

### Add --list-defs Feature
Solves the chicken-and-egg problem: users need to know what defs to put in
their location file, but --defs requires a working platform/location/spec tuple.

New flag: `mkosimage --list-defs <platform>` — loads platform JSON, parses
all `>>var<<` references, and lists them with defaults. No location or spec
required.

## Documentation Approach: MkDocs + GitHub Pages

### Why MkDocs over GitHub Wiki
- Lives in repo, versioned with code
- Spec reference tables can be auto-generated from JSON
- `mkdocs gh-deploy` publishes to sshoecraft.github.io/osimager
- PR review process for doc changes
- Search built-in

### Setup
- `mkdocs.yml` config at project root
- `docs/` folder for markdown source
- MkDocs-Material theme
- GitHub Action for auto-deploy on push to main

## Documentation Pages

### Hand-Written Pages

**Home (index.md)**
- What osimager is, what it does
- Quick overview of the platform/location/spec model
- Links to getting started

**Installation (installation.md)**
- pip install osimager
- Packer prerequisites and plugin installation per platform
- Python version requirements

**Getting Started (getting-started.md)**
- Quickstart walkthrough: copy example location, set credentials, first build
- The platform/location/spec tuple concept
- Basic mkosimage usage

**Location Setup (location-setup.md)**
- TOML and JSON formats side by side
- Every field explained with real values
- platform_specific sections with examples
- How defs flow: all.json → platform → location → spec → version_specific → platform_specific

**Credential Setup (credential-setup.md)**
- credential_source: "vault" vs "config"
- Vault mode: vault_addr, vault_token
- Config mode: ~/.config/osimager/secrets file format
- Per-platform credential requirements (vsphere, proxmox, azure, gcp, aws)

**Platform Reference (platform-reference.md)**
- Each platform explained: what it is, when to use it, required Packer plugin
- Two categories: ISO-boot platforms vs cloud-image platforms
- Per-platform defs table (auto-generated or maintained alongside platform JSON)
- Per-platform location example snippets

**CLI Reference (cli-reference.md)**
- mkosimage: all flags (--list, --defs, --list-defs, --dry-run, --define, --set, etc.)
- rfosimage: flags and usage
- mkvenv: flags and usage

**Spec Authoring (spec-authoring.md)**
- How to create/modify specs
- Template substitution syntax: >>var<<, %>var<%, #>expr<#, E>expr<E, |>path<|, 5>path<5, 6>path<6, [>name<]
- version_specific and platform_specific nesting
- The include mechanism
- The merge system and the "merge" key
- required_files array

### Auto-Generated Pages

**Supported OS (supported-os.md)**
- Script reads all spec JSON files
- Generates table: distro, version range, architectures, installer type, platforms supported
- Shows which cloud platforms have image refs configured
- Never goes stale

**Defs Reference (defs-reference.md)**
- Script parses platform JSON files for >>var<< references
- Generates per-platform table of all defs with defaults
- Cross-references with spec defs
- Categories: common (all platforms), ISO-only, cloud-only, platform-specific

## Generation Script

`docs/generate.py` — reads spec and platform JSON, produces markdown:
- Walks osimager/data/specs/*/spec.json → supported OS table
- Walks osimager/data/platforms/*.json → defs reference tables
- Parses >>var<<, %>var<%, #>expr<# patterns to extract referenced defs
- Output goes to docs/ as .md files
- Run before mkdocs build (can be wired into mkdocs hook or CI)

## Sidebar / Navigation Structure

```yaml
nav:
  - Home: index.md
  - Installation: installation.md
  - Getting Started: getting-started.md
  - Configuration:
    - Location Setup: location-setup.md
    - Credential Setup: credential-setup.md
  - Reference:
    - CLI Reference: cli-reference.md
    - Platform Reference: platform-reference.md
    - Spec Authoring: spec-authoring.md
    - Defs Reference: defs-reference.md
    - Supported OS: supported-os.md
```

## Order of Work

1. Add missing platforms + spec platform_specific entries
2. Add --list-defs feature
3. Set up MkDocs scaffolding (mkdocs.yml, docs/ folder, theme)
4. Write generation script (docs/generate.py)
5. Write hand-authored pages (start with Getting Started and Location Setup)
6. Generate auto pages (Supported OS, Defs Reference)
7. Set up GitHub Pages deploy action
8. Update README to point to new docs URL
