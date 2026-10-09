# Changelog

All notable changes to OSImager are documented here. The format is based on
[Keep a Changelog](https://keepachangelog.com/), and the project aims to follow
[Semantic Versioning](https://semver.org/).

> **Note on versioning:** the version is the `OSIMAGER_VERSION` string in
> `osimager/core.py`. Starting with 1.9.0, releases are git-tagged `vX.Y.Z`, and
> pushing a tag publishes that release to PyPI. Versions before 1.9.0 were
> development milestones that were never tagged or published. Some versions
> were never released at all: 1.9.2 was folded into 1.9.3. There is no 1.6.x —
> the version went 1.5.0 → 1.7.0 during the data-separation work.

## [1.10.1] — 2026-10-09

### Changed
- **`iso_path` comes only from the global settings.** It is a directory on the
  machine running OSImager, and every Packer field it feeds (`iso_url` for a
  local ISO, `iso_target_path` for a download) is a path on that machine. It
  doesn't change with the location. Locations could still override it, though,
  even after 1.5.0 moved it to global settings. That let a build and the `-a`
  listing disagree about what was present, made `--local` with a `-latest`
  target check the wrong directory, and left a location pointing at a directory
  that didn't exist. A location that still sets `iso_path` now gets a warning,
  and its value is ignored. Set it with `mkosimage --set iso_path=...`. The
  location examples in the docs no longer include it.

### Removed
- **`-c/--config`.** It never had any effect, because settings were always read
  from `~/.config/osimager/config.json`. Swapping only that file wouldn't be
  enough anyway: `locations/`, `platforms/` and `secrets` live in the same
  directory. To use a different config set, use `XDG_CONFIG_HOME`.

## [1.10.0] — 2026-10-09

### Added
- **`<dist>-latest-<arch>` targets.** For example,
  `mkosimage proxmox/pve/alma-latest-x86_64` builds the highest version the
  alma spec provides for x86_64, currently 10.2, so you don't need to know the
  current release number. The alias is resolved to the real version before the
  build starts. The build config, the default instance name and the logs carry
  `alma-10.2-x86_64`, and the resolution is printed. With `--local`, the alias
  resolves to the newest version whose ISO is already local. The alias reflects
  what the specs provide, not what the vendor ships, so a new upstream release
  still needs a spec update.
- **`--latest`** lists only the `<dist>-latest-<arch>` targets and the spec each
  resolves to. Combined with `--avail` or `--local`, it limits the availability
  report to those specs. `--list` itself is unchanged.
- **AlmaLinux 9.8 and 10.2** (x86_64, aarch64), downloading from
  `repo.almalinux.org`.
- **Newer releases across the specs.** Every new URL was checked and returns 200.
  - **Rocky:** 8.10, 9.8
  - **Oracle Linux:** 9.8, 10.2
  - **RHEL:** 9.8
  - **Fedora:** 44
  - **Debian:** 12.14, 12.15, 13.6, 13.7
  - **Ubuntu:** 24.04.4, 24.04.5, 26.04.1
  - **Linux Mint:** 22.3
  - **MX Linux:** 23.6
  - **Alpine:** 3.22, 3.23, 3.24
  - **FreeBSD:** 14.5, 15.1
  - **NetBSD:** 10.2
  - **OpenBSD:** 7.7, 7.8, 7.9
  - **DragonFly:** 6.4.2
  - **Proxmox VE:** 9.2

### Changed
- **`--avail` and `--local` print one list.** The separate Local and Download
  sections are gone. Each line's source column already says where the ISO is:
  a path means it's present, a URL means it would be downloaded. Specs are
  listed in version order. Specs that can't be built are not listed or counted,
  and there is no summary line. Disk-image specs are now listed when their
  image is present; before, they never appeared.
- **`--list` is in version order**, the same as `--avail`, so `alma-8.10` comes
  before `alma-10.0`.
- **The CLI reference is rewritten from the code.** Every option now says
  exactly what it does. The reference had several errors: exit codes 2–5,
  which don't exist; `--local-only` described as persisted, when it applies to
  one run; `-k` described as keeping only temp files; the wrong
  `packer_cache_dir` default; a non-existent `disk_size` def. It now notes that
  `-c/--config` is accepted but has no effect, and that `--set` saves to
  `config.json`. The README's option list is grouped by purpose and links to
  the full reference, and the getting-started examples show real output.
- **XCP-ng 8.3** downloads the refreshed 2026-08-06 installer ISO.
- **Releases that no longer exist upstream are now local-only** (`file://` in
  `iso_path`). They build if the ISO is placed there and otherwise show as not
  available, instead of failing `--check-urls`. This covers DragonFly 6.4 (only
  a `.bz2` of the ISO is left) and Proxmox VE 5.4, 6.4 and 9.0 (removed from
  every Proxmox mirror).

### Removed
- **Flatcar stable aarch64.** Flatcar has never published an arm64 installer
  ISO, so the entry pointed at a URL that never existed.

### Fixed
- **AlmaLinux 9.7 and 10.1 ISO downloads returned 404.** When AlmaLinux ships a
  new point release, it moves the previous one off `repo.almalinux.org` and into
  `vault.almalinux.org`. 9.8 and 10.2 replaced 9.7 and 10.1 this way. Those two
  versions now download from the vault.
- **Other ISO downloads that returned 404 now point at the vendor's archive:**
  - **Rocky 9.7:** `dl.rockylinux.org/vault`
  - **Debian 13.5:** `cdimage.debian.org/cdimage/archive`
  - **NetBSD 10.1:** `archive.netbsd.org`
  - **OpenBSD 7.6:** `ftp.eu.openbsd.org`
  - **openSUSE Leap 16.0:** now uses the `offline/` installer ISO, since the old
    DVD path and the `ports/` aarch64 path no longer exist.
- **OpenBSD installs fetched their sets from `cdn.openbsd.org` regardless of
  version.** The CDN keeps only recent releases, so a 7.6 install failed at the
  sets step even with a working ISO. `install.conf` now uses the spec's
  `obsd_mirror`, which is the archive mirror for 7.6 and the CDN for newer
  releases.

## [1.9.3] — 2026-10-06

### Fixed
- **Proxmox builds hung forever at "Waiting for SSH to become available".**
  For the proxmox platform, the ssh spec's `ssh_host` fell through to
  `{{ .Host }}`. The proxmox-iso builder has no `.Host`, so packer rendered it
  as the literal string `<no value>` and kept dialing that name, even though
  the VM was up on the network. Proxmox now gets an empty `ssh_host`. That
  makes the builder read the VM's address from the QEMU guest agent, which the
  platform already enables with `qemu_agent: true`.

## [1.9.2] — 2026-09-25

### Fixed
- **Debian 13 builds stalled at "apt configuration problem" or a DVD prompt.**
  The seed's `early_command` copied `debian.fix` from `/media`, which only works
  if a timed boot keystroke has already mounted the seed CD there. On a slow
  host the keystroke loses that race, and because every failure was masked with
  `|| true`, the fix was silently never installed. The stock media scan then
  failed. The early command now mounts the seed CD by its label when `/media`
  doesn't have the fix. If the copy still fails, the installer stops with an
  error right there. This applies to the Debian 9, 10–11, 12 and 13 seeds.
- **The `40cdrom` replacement in `debian.fix` left apt without the DVD.** It
  only rewrote `sources.list`. It didn't bind `/cdrom` into
  `/target/media/cdrom` or write apt's `00CDMountPoint`/`00NoMountCDROM`
  config, so software selection asked for the DVD again. The replacement now
  sets up the same state as Debian's base-installer, and it does so
  idempotently. apt no longer mounts or probes drives itself, so the seed CD in
  the second drive can no longer confuse the scan.
- **Debian 13 package installation failed on packages the DVD doesn't carry.**
  `tmux`, `open-vm-tools` and `qemu-guest-agent` are not on the Debian 13
  DVD-1, and the install uses no network mirror. They are removed from
  `pkgsel/include` in `debian.seed`.
- The 25-minute parallel Debian 13 builds were not slow. Each one was sitting
  at the first of those dialogs.

## [1.9.1] — 2026-09-23

### Fixed
- **RHEL 9 and 10 qemu builds kernel-panicked about 26 seconds into the
  installer** (`Attempted to kill init! exitcode=0x00007f00`). The build VM got
  QEMU's default `qemu64` CPU model, which only has the baseline x86-64
  instruction set. RHEL 9 is built for x86-64-v2 and RHEL 10 for x86-64-v3, so
  glibc refused to start and init exited 127. The qemu platform now sets
  `cpu_model` to `host` under KVM and `max` without it, so the guest sees the
  real CPU's features. This covers bridged and non-bridged builds alike. The
  finished VM was already fine: its libvirt domain uses `host-passthrough`.
- **Local-only ISOs in vendor subdirectories were never found.** 64 spec
  `file://` URLs pointed at `<iso_path>/<Vendor>/<file>` (`RedHat/`,
  `AlmaLinux/`, `Debian/`, `SUSE/`, `Windows/`, `OracleLinux/` and others),
  while ISOs live flat in `iso_path` and every platform builds the path as
  `<iso_path>/<iso_name>`. `--local --avail` hid those targets and the build
  pre-flight rejected them ("ISO file not found") even with the ISO present.
  All spec ISO paths are now flat.

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
