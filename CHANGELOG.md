# Changelog

All notable changes to OSImager are documented here. The format is based on
[Keep a Changelog](https://keepachangelog.com/), and the project aims to follow
[Semantic Versioning](https://semver.org/).

> **Note on versioning:** these version numbers are development milestones, not
> published releases. The project has never been git-tagged or published to
> PyPI; the version is the `OSIMAGER_VERSION` string in `osimager/core.py`,
> bumped per change. There is no 1.6.x — the version went 1.5.0 → 1.7.0 during
> the data-separation work.

## [1.9.0] — 2026-09-23

### Changed
- **Baseline data ships inside the engine again.** Specs, platforms, installer
  files, Ansible tasks, build-hook scripts, `ansible.json` and examples moved
  from the separate `osimager-data` package into `osimager/data/`, installed as
  package data. Keeping two packages in step was more work than releasing them
  together, and the separate release cadence it was meant to allow never
  mattered. `system_data_dir` now always points at `osimager/data/`;
  `osimager_data` is no longer imported. `~/.config/osimager/` overrides still
  win over the baseline.
- CLI "no specs / no platforms / no ansible.json" messages name the bundled data
  directory instead of telling the user to `pip install osimager-data`.
- `docs/generate.py` reads data from `osimager/data/` in the source tree.
- The data repo's design notes moved to `docs/data/`.
- RHEL 10.x x86_64 now downloads its DVD from archive.org
  (`rhel-<version>-x86_64-resources`) instead of requiring a local copy under
  `<iso_path>/RedHat/`. aarch64 remains local-only; archive.org has no RHEL 10
  aarch64 DVD.

### Fixed
- **Documentation site deploy had failed on every push since 1.7.0.**
  `docs/generate.py` imported `osimager_data`, which the docs workflow never
  installs, so the job died before `mkdocs gh-deploy`. It now reads the bundled
  `osimager/data/`. The QEMU libvirt-URI and Photon kickstart notes are in the
  nav under Architecture.
- **GitHub Actions moved off Node 20**, which GitHub removed from its runners
  on 2026-09-16: `actions/checkout` v4 → v7 and `actions/setup-python` v5 → v7
  in both the docs and PyPI publish workflows.
- **Installed packages were missing four data files**: `files/alpine/answerfile`,
  `files/openbsd/install.conf`, and `files/ignition/{fcos,flatcar}.ign`. The old
  data package listed package-data by extension, and these have none or `.ign`,
  so Alpine, OpenBSD, Fedora CoreOS and Flatcar builds could only work from an
  editable install. Package data is now everything under `osimager/data/`
  except bytecode.
- **RHEL 8 qemu builds failed at launch** with `qemu: could not load PC BIOS
  'efi'`. The `8.*` spec block set `firmware: efi` under `config`, which is
  passed verbatim to Packer's qemu `firmware` option (a firmware file path). It
  now declares `firmware: efi` under `defs` with a `bios` firmware-specific
  boot command, the same shape as RHEL 9/10, and the proxmox override that only
  existed to blank the `config` key is gone.

## [1.8.0] — 2026-06-13

### Added
- **Disk-image import builds.** Appliances that ship a prebuilt image
  (qcow2/vmdk/ova) instead of an installer ISO can now be indexed and built.
  - `resolve_disk_image_url(data, version, arch)` — sibling of
    `resolve_iso_url()`; both now delegate to a shared
    `resolve_url_field(data, version, arch, field)`.
  - `make_index()` indexes a spec/version/arch when it provides an installer ISO
    **or** a `disk_image_url`. Disk-image entries carry `disk_image_url`,
    `disk_image_local`, and `image_import: true`.
  - `make_build()` derives `disk_image_name` and sets the `image_import` def so
    platform builder templates can branch on it.
  - `docs/generate.py` architecture derivation counts disk-image-only specs
    (`iso_url` *or* `disk_image_url` makes an arch buildable).
- **Per-spec build hooks.** `run_build_hooks(name)` runs `pre_build`/`post_build`
  scripts declared by the **spec** first, then the **platform** (previously only
  platform-level `pre_build`/`post_build` were honored). Data-side contract: a
  spec or platform JSON declares `"pre_build": "scripts/<name>.py"` (or
  `post_build`); the script exposes `def run(osimager)` and reads `osimager.defs`.

### Changed
- `pre_build` hooks now run **before** the Packer build JSON is written, so a
  hook may transform the ISO/disk image (e.g. `coreos-installer iso customize`
  to bake an Ignition config for Fedora CoreOS / Flatcar) and adjust
  `self.config`/`self.defs` before Packer consumes the artifact.

## [1.7.0] — 2026-06-13

### Changed
- **Engine and data separated.** The engine repo no longer ships any data; all
  specs, platforms, installer files, Ansible tasks, and examples live in a
  separate `osimager_data` package, resolved at runtime.
- **Two-layer data resolution.** `~/.config/osimager/` (specs, platforms, files,
  scripts, `ansible.json`) overrides the `osimager_data` package baseline via
  `resolve_data_path()` / `resolve_data_files()`.
- All directories follow XDG base-directory paths (config, data/venvs, cache).
- Fixed venv hoisting from `version_specific` entries.

### Removed
- `osimager/constants.py` — `OSIMAGER_VERSION` and exit codes now live in
  `osimager/core.py`; `pyproject` reads the version from there and no longer
  ships package-data globs.

### Documentation
- Removed obsolete pre-MkDocs files left in `docs/`; fixed the example-copy
  command (now resolves via `osimager_data.DATA_DIR`); corrected architecture
  and reference pages to the engine/data split.
- `docs/generate.py`: reads `osimager_data.DATA_DIR`; derives architectures from
  `arch_specific` ISO-URL availability (`provides.arches` was removed in 1.5.0).
- `docs/generate.py` installer detection recognizes the JSON/answer-file
  installers — ignition (CoreOS/Flatcar), archinstall (Arch), agama
  (openSUSE Leap 16), OpenBSD `install.conf`, Photon JSON-kickstart, Alpine
  answerfile — and labels `answer.toml` (Proxmox VE) and `answerfile.xml`
  (XCP-ng), which were previously reported as `none`.
- `docs/generate.py` counts every `specs/*/` directory with a `provides`
  section instead of a fixed list (generated catalog: 20 distributions, 524
  specs). README counts reconciled with the generated reality.

## [1.5.0] — 2026-03-01

### Changed
- Config format changed from INI (configparser) to JSON (`config.json`).
- `iso_path` moved from per-location defs to global settings.
- Architectures are derived at index time by probing `resolve_iso_url()` rather
  than declared. Specs use `arch_specific` entries with explicit per-arch
  `iso_url`, and `"iso_url": ""` blocks an unsupported arch.

### Removed
- `provides.arches` and `version_specific[].arches`.

### Added
- Expanded OS coverage; core refactor.

## [1.4.4] — 2026-02-14

### Added
- `--check-urls` maintenance URL checker (parallel HEAD requests).
- `--avail` ISO-availability report.
- Pre-build ISO validation (`check_iso_url()`).

### Changed
- `resolve_iso_url()` handles `arch_specific` overrides and `E>...<E` expression
  evaluation.

### Removed
- `save_index` / on-disk index file caching (the index is always built fresh).

## [1.4.1] — 2026-02-13

### Added
- `--list-platforms` and `--list-defs` CLI flags.
- `--init-plugins` (installs required Packer plugins from the `plugin` key in
  platform JSON files); `--show-config`.
- Packer prerequisite check; `cp` command hint for `example-secrets`.

### Fixed
- ISO URL fixes across all distros; `file://` placeholders for ISOs that are not
  publicly downloadable.

## [1.4.0] — 2026-02-13

### Added
- MkDocs + Material documentation, deployed to GitHub Pages.

## [1.3.0] — 2026-02-13

### Added
- Cloud platforms (AWS, Azure, GCP) and additional hypervisors.
- Updated distribution versions.

## [1.2.0] — 2026-02-13

### Added
- Refactor to a proper Python package.
- TOML location support.
- User config system under `~/.config/osimager/`.

## [1.1.0]

### Added
- User config system groundwork (`~/.config/osimager/`), `credential_source`
  (vault/config).
- Contextual no-target help with setup guidance.

## [1.0.0]

### Added
- Initial package refactor from the legacy `lib/osimager/` tree.
